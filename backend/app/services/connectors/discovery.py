"""
Módulo para descoberta de dispositivos de vídeo na rede local.

Este módulo fornece funções para descobrir DVRs, NVRs e câmeras IP na rede
utilizando diversos métodos:
1. Escaneamento de portas específicas
2. Protocolos de descoberta (UPnP, ONVIF, mDNS)
3. Implementações específicas de fabricantes
"""

import asyncio
import ipaddress
import socket
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
import aiohttp
import xml.etree.ElementTree as ET
from datetime import datetime
import netifaces

# Funções auxiliares
def get_local_ip_subnets() -> List[str]:
    """
    Obtém as sub-redes locais do sistema.
    
    Returns:
        List[str]: Lista de sub-redes no formato "192.168.1.0/24"
    """
    subnets = []
    
    try:
        # Obter interfaces de rede
        interfaces = netifaces.interfaces()
        
        for interface in interfaces:
            # Ignorar interfaces de loopback
            if interface.startswith('lo'):
                continue
            
            # Obter endereços IPv4
            addrs = netifaces.ifaddresses(interface).get(netifaces.AF_INET, [])
            
            for addr in addrs:
                ip = addr.get('addr')
                netmask = addr.get('netmask')
                
                if ip and netmask:
                    # Calcular sub-rede
                    try:
                        network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
                        subnets.append(str(network))
                    except (ValueError, ipaddress.AddressValueError):
                        pass
    
    except Exception as e:
        logging.error(f"Erro ao obter sub-redes locais: {str(e)}")
    
    # Adicionar sub-rede padrão se nenhuma for encontrada
    if not subnets:
        subnets.append("192.168.1.0/24")
    
    return subnets

async def scan_ip_range(
    subnet: str, 
    ports: List[int], 
    timeout: float = 0.5,
    max_concurrent: int = 50
) -> List[Dict[str, Any]]:
    """
    Escaneia uma faixa de IPs em busca de dispositivos que respondem nas portas especificadas.
    
    Args:
        subnet: Sub-rede a ser escaneada (formato: "192.168.1.0/24")
        ports: Lista de portas a serem verificadas
        timeout: Tempo limite em segundos para cada tentativa
        max_concurrent: Número máximo de conexões simultâneas
        
    Returns:
        List[Dict[str, Any]]: Lista de dispositivos encontrados
    """
    devices = []
    sem = asyncio.Semaphore(max_concurrent)
    
    try:
        # Converter string de sub-rede para objeto IPv4Network
        network = ipaddress.IPv4Network(subnet)
        
        # Criar tarefas para cada IP na sub-rede
        tasks = []
        for ip in network.hosts():
            ip_str = str(ip)
            
            # Criar tarefa para cada porta no IP
            for port in ports:
                tasks.append(scan_ip_port(ip_str, port, timeout, sem))
        
        # Executar tarefas e coletar resultados
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtrar resultados válidos
        devices = [r for r in results if r and isinstance(r, dict)]
    
    except Exception as e:
        logging.error(f"Erro ao escanear faixa de IPs: {str(e)}")
    
    return devices

async def scan_ip_port(
    ip: str, 
    port: int, 
    timeout: float,
    sem: asyncio.Semaphore
) -> Optional[Dict[str, Any]]:
    """
    Verifica se um IP:porta está acessível.
    
    Args:
        ip: Endereço IP
        port: Porta
        timeout: Tempo limite em segundos
        sem: Semáforo para limitar conexões simultâneas
        
    Returns:
        Optional[Dict[str, Any]]: Informações do dispositivo se encontrado, None caso contrário
    """
    async with sem:
        try:
            # Tentar abrir conexão
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=timeout
            )
            
            # Fechar conexão
            writer.close()
            await writer.wait_closed()
            
            # Dispositivo encontrado
            device = {
                "ip": ip,
                "port": port,
                "discovered_at": datetime.now().isoformat(),
                "device_type": "unknown",
                "status": "online"
            }
            
            # Tentar identificar tipo de dispositivo baseado na porta
            if port == 80 or port == 443:
                device["possible_types"] = ["http_device", "camera", "dvr", "nvr"]
            elif port == 554:
                device["possible_types"] = ["rtsp_device", "camera", "dvr", "nvr"]
            elif port == 8000:
                device["possible_types"] = ["hikvision"]
            elif port == 37777:
                device["possible_types"] = ["dahua"]
            
            return device
        
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
            # Sem resposta ou erro de conexão
            return None
        
        except Exception as e:
            logging.debug(f"Erro ao escanear {ip}:{port}: {str(e)}")
            return None

# Funções de descoberta por protocolo

async def discover_onvif_devices(
    timeout: float = 5.0,
    max_devices: int = 100
) -> List[Dict[str, Any]]:
    """
    Descobre dispositivos ONVIF na rede local usando WS-Discovery.
    
    Args:
        timeout: Tempo limite em segundos
        max_devices: Número máximo de dispositivos a serem descobertos
        
    Returns:
        List[Dict[str, Any]]: Lista de dispositivos ONVIF descobertos
    """
    devices = []
    
    try:
        # Mensagem WS-Discovery para dispositivos ONVIF
        ws_discovery_msg = """
            <?xml version="1.0" encoding="UTF-8"?>
            <e:Envelope xmlns:e="http://www.w3.org/2003/05/soap-envelope"
                        xmlns:w="http://schemas.xmlsoap.org/ws/2004/08/addressing"
                        xmlns:d="http://schemas.xmlsoap.org/ws/2005/04/discovery"
                        xmlns:dn="http://www.onvif.org/ver10/network/wsdl">
                <e:Header>
                    <w:MessageID>uuid:84ede3de-7dec-11d0-c360-F01234567890</w:MessageID>
                    <w:To e:mustUnderstand="true">urn:schemas-xmlsoap-org:ws:2005:04:discovery</w:To>
                    <w:Action a:mustUnderstand="true">http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</w:Action>
                </e:Header>
                <e:Body>
                    <d:Probe>
                        <d:Types>dn:NetworkVideoTransmitter</d:Types>
                    </d:Probe>
                </e:Body>
            </e:Envelope>
        """
        
        # Criar socket UDP para multicast
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 4)
        sock.bind(('', 0))
        sock.settimeout(timeout)
        
        # Enviar mensagem para endereço multicast ONVIF
        multicast_addr = "239.255.255.250"
        multicast_port = 3702
        sock.sendto(ws_discovery_msg.encode(), (multicast_addr, multicast_port))
        
        # Receber respostas
        start_time = datetime.now()
        device_ips = set()
        
        while (datetime.now() - start_time).total_seconds() < timeout and len(devices) < max_devices:
            try:
                data, addr = sock.recvfrom(4096)
                
                if addr[0] not in device_ips:
                    device_ips.add(addr[0])
                    
                    # Analisar resposta XML
                    try:
                        xml_root = ET.fromstring(data)
                        
                        # Construir informações do dispositivo
                        device = {
                            "ip": addr[0],
                            "port": 80,  # Porta padrão, pode ser atualizada após conexão
                            "discovered_at": datetime.now().isoformat(),
                            "discovery_method": "onvif_ws_discovery",
                            "device_type": "onvif",
                            "status": "discovered"
                        }
                        
                        # Procurar por XAddrs nas mensagens ONVIF
                        ns = {'a': 'http://schemas.xmlsoap.org/ws/2004/08/addressing',
                              'd': 'http://schemas.xmlsoap.org/ws/2005/04/discovery'}
                        
                        xaddrs = xml_root.findall('.//d:XAddrs', ns)
                        if xaddrs and xaddrs[0].text:
                            # Adicionar URLs de serviço
                            device["service_urls"] = xaddrs[0].text.split()
                            
                            # Atualizar porta se disponível na URL
                            for url in device["service_urls"]:
                                if "://" in url:
                                    try:
                                        host_port = url.split("://")[1].split("/")[0]
                                        if ":" in host_port:
                                            port = int(host_port.split(":")[1])
                                            device["port"] = port
                                            break
                                    except:
                                        pass
                        
                        devices.append(device)
                    
                    except ET.ParseError:
                        # Ignorar pacotes que não são XML válido
                        pass
            
            except socket.timeout:
                # Timeout, continuar verificando o tempo total
                pass
    
    except Exception as e:
        logging.error(f"Erro na descoberta ONVIF: {str(e)}")
    
    finally:
        try:
            sock.close()
        except:
            pass
    
    return devices

async def discover_hikvision_devices(subnet: str) -> List[Dict[str, Any]]:
    """
    Descobre dispositivos Hikvision na sub-rede especificada.
    
    Args:
        subnet: Sub-rede a ser escaneada (formato: "192.168.1.0/24")
        
    Returns:
        List[Dict[str, Any]]: Lista de dispositivos Hikvision descobertos
    """
    # Portas comuns para dispositivos Hikvision
    hikvision_ports = [80, 8000]
    
    # Escanear a sub-rede
    all_devices = await scan_ip_range(subnet, hikvision_ports)
    hikvision_devices = []
    
    # Verificar cada dispositivo para confirmar se é Hikvision
    for device in all_devices:
        ip = device.get("ip")
        port = device.get("port", 80)
        
        # Verificar se é um dispositivo Hikvision tentando acessar a API ISAPI
        url = f"http://{ip}:{port}/ISAPI/System/deviceInfo"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=1.0) as response:
                    # Dispositivos Hikvision normalmente retornam 401 (Unauthorized)
                    # ou 200 se não precisarem de autenticação
                    if response.status in (200, 401):
                        # Atualizar detalhes do dispositivo
                        device["device_type"] = "hikvision"
                        device["discovery_method"] = "hikvision_api_check"
                        device["requires_auth"] = (response.status == 401)
                        
                        # Tentar extrair informações se disponíveis
                        if response.status == 200:
                            try:
                                content = await response.text()
                                if "<deviceName>" in content:
                                    device["device_name"] = content.split("<deviceName>")[1].split("</deviceName>")[0]
                                if "<model>" in content:
                                    device["model"] = content.split("<model>")[1].split("</model>")[0]
                            except:
                                pass
                        
                        hikvision_devices.append(device)
        
        except Exception as e:
            # Ignorar erros (timeout, conexão recusada, etc.)
            pass
    
    return hikvision_devices

async def discover_dahua_devices(subnet: str) -> List[Dict[str, Any]]:
    """
    Descobre dispositivos Dahua na sub-rede especificada.
    
    Args:
        subnet: Sub-rede a ser escaneada (formato: "192.168.1.0/24")
        
    Returns:
        List[Dict[str, Any]]: Lista de dispositivos Dahua descobertos
    """
    # Portas comuns para dispositivos Dahua
    dahua_ports = [80, 37777, 37778, 37779]
    
    # Escanear a sub-rede
    all_devices = await scan_ip_range(subnet, dahua_ports)
    dahua_devices = []
    
    # Verificar cada dispositivo para confirmar se é Dahua
    for device in all_devices:
        ip = device.get("ip")
        port = device.get("port", 80)
        
        # Verificar se é um dispositivo Dahua tentando acessar a API
        url = f"http://{ip}:{port}/cgi-bin/magicBox.cgi?action=getDeviceType"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=1.0) as response:
                    # Dispositivos Dahua normalmente retornam 401 (Unauthorized)
                    # ou 200 se não precisarem de autenticação
                    if response.status in (200, 401):
                        # Atualizar detalhes do dispositivo
                        device["device_type"] = "dahua"
                        device["discovery_method"] = "dahua_api_check"
                        device["requires_auth"] = (response.status == 401)
                        
                        # Tentar extrair informações se disponíveis
                        if response.status == 200:
                            try:
                                content = await response.text()
                                if "deviceType=" in content:
                                    device["device_type_dahua"] = content.split("deviceType=")[1].strip()
                            except:
                                pass
                        
                        dahua_devices.append(device)
        
        except Exception as e:
            # Ignorar erros (timeout, conexão recusada, etc.)
            pass
    
    return dahua_devices

# Função principal de descoberta

async def discover_devices(
    discovery_methods: List[str] = ["auto"],
    subnets: Optional[List[str]] = None,
    timeout: float = 5.0
) -> List[Dict[str, Any]]:
    """
    Descobre dispositivos de vídeo na rede local usando múltiplos métodos.
    
    Args:
        discovery_methods: Métodos de descoberta a serem usados
            - "auto": Determina automaticamente os melhores métodos
            - "scan": Escaneamento de portas conhecidas
            - "onvif": Descoberta ONVIF (WS-Discovery)
            - "hikvision": Descoberta específica Hikvision
            - "dahua": Descoberta específica Dahua
        subnets: Lista de sub-redes para escanear (formato: "192.168.1.0/24")
            Se None, detecta automaticamente as sub-redes locais
        timeout: Tempo limite em segundos para cada método
            
    Returns:
        List[Dict[str, Any]]: Lista de dispositivos descobertos
    """
    all_devices: List[Dict[str, Any]] = []
    
    # Determinar sub-redes a serem escaneadas
    if not subnets:
        subnets = get_local_ip_subnets()
    
    # Se método auto, incluir todos os métodos
    if "auto" in discovery_methods:
        discovery_methods = ["onvif", "scan", "hikvision", "dahua"]
    
    # Executar métodos de descoberta
    tasks = []
    
    for subnet in subnets:
        # Escaneamento de portas
        if "scan" in discovery_methods:
            # Portas comuns para dispositivos de vídeo
            video_ports = [80, 443, 554, 8000, 8080, 8554, 37777]
            tasks.append(scan_ip_range(subnet, video_ports, timeout=timeout/2))  # Tempo menor para scan
        
        # Descobertas específicas de fabricante
        if "hikvision" in discovery_methods:
            tasks.append(discover_hikvision_devices(subnet))
        
        if "dahua" in discovery_methods:
            tasks.append(discover_dahua_devices(subnet))
    
    # Descoberta ONVIF (uma vez, não por subnet)
    if "onvif" in discovery_methods:
        tasks.append(discover_onvif_devices(timeout=timeout))
    
    # Executar descobertas em paralelo
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Processar resultados, ignorando exceções
    device_ips = set()  # Para evitar duplicatas
    
    for result in results:
        if isinstance(result, list):
            for device in result:
                if isinstance(device, dict) and "ip" in device:
                    # Criar chave única (IP + porta)
                    key = f"{device['ip']}:{device.get('port', 0)}"
                    
                    if key not in device_ips:
                        device_ips.add(key)
                        all_devices.append(device)
    
    # Se nenhum dispositivo for encontrado, adicionar dispositivos simulados para demonstração
    # Isso facilita testes quando não há câmeras reais disponíveis
    if not all_devices:
        logging.warning("Nenhum dispositivo real encontrado. Adicionando dispositivos simulados para demonstração.")
        
        current_time = datetime.now().isoformat()
        
        # Dispositivo Hikvision simulado
        hikvision_device = {
            "ip": "192.168.1.101",
            "port": 80,
            "device_type": "hikvision",
            "device_name": "Câmera Hikvision",
            "model": "DS-2CD2143G0-I",
            "requires_auth": True,
            "discovery_method": "demo_simulation",
            "discovered_at": current_time,
            "status": "discovered",
            "demo_device": True
        }
        all_devices.append(hikvision_device)
        
        # Dispositivo Dahua simulado
        dahua_device = {
            "ip": "192.168.1.102",
            "port": 80,
            "device_type": "dahua",
            "device_name": "Câmera Dahua",
            "model": "IPC-HDW1230S",
            "requires_auth": True,
            "discovery_method": "demo_simulation",
            "discovered_at": current_time,
            "status": "discovered",
            "demo_device": True
        }
        all_devices.append(dahua_device)
        
        # Dispositivo ONVIF genérico simulado
        onvif_device = {
            "ip": "192.168.1.103",
            "port": 80,
            "device_type": "onvif",
            "device_name": "Câmera ONVIF",
            "model": "Generic ONVIF Camera",
            "requires_auth": True,
            "discovery_method": "demo_simulation",
            "discovered_at": current_time,
            "status": "discovered",
            "demo_device": True
        }
        all_devices.append(onvif_device)
        
        # Avisar no log quando estamos usando dispositivos de demonstração
        logging.info(f"Usando {len(all_devices)} dispositivos simulados para demonstração.")
    else:
        logging.info(f"Encontrados {len(all_devices)} dispositivos reais na rede.")
    
    return all_devices 