# Detec-O: Implementações Recentes e Plano de Funcionalidades Futuras

## 1. Melhorias Implementadas Recentemente

### 1.1. Correções de Interface (UI Fixes)

Foram implementadas correções importantes na interface do usuário:

- **Correção da tela branca durante navegação**: Implementado componente `ScrollToTop` que garante renderização adequada ao alternar entre páginas.
- **Eliminação de scroll horizontal**: Adicionado CSS para controlar overflow e garantir que o conteúdo se ajuste à largura da tela.
- **Melhorias para dispositivos móveis**: Espaçamento adequado no final das páginas para garantir que o conteúdo não seja coberto em dispositivos móveis.
- **Reestruturação de componentes chave**: 
  - Criação de um novo componente `Navbar` mais responsivo.
  - Revisão do `MainLayout` para melhor organização de conteúdo.
  - Ajustes no `ZoneEditor` para garantir exibição adequada em todas as telas.

### 1.2. Funcionalidades de Backend

#### Processamento de Vídeo

- Desenvolvido serviço `VideoProcessor` para conexão com câmeras físicas via protocolos ONVIF/Hikvision.
- Implementada detecção em tempo real usando modelos YOLO.
- Criado sistema de configuração por câmera para diferentes modelos de IA.
- Adicionado suporte para zonas de detecção personalizáveis.

#### API e Sistema de Dados

- Criadas rotas completas para gerenciamento de câmeras e configurações.
- Implementada persistência de dados usando SQLAlchemy.
- Adicionado suporte para configurações de AI por câmera.
- Desenvolvido sistema de logging para monitoramento.

## 2. Implementação de Reconhecimento Facial

### 2.1. Estrutura Inicial (Já Implementada)

Foi implementada a estrutura básica para reconhecimento facial:

- **Modelo de Pessoa**: Criada entidade `Person` com os seguintes atributos:
  - ID único
  - Nome
  - Descrição
  - Categoria (funcionário, visitante, etc.)
  - Timestamps de criação e atualização
  - Contagem de faces registradas

- **API de Gerenciamento de Pessoas**:
  - `GET /api/v1/persons`: Listar pessoas cadastradas
  - `POST /api/v1/persons`: Criar nova pessoa com face
  - `GET /api/v1/persons/{id}`: Obter detalhes de uma pessoa
  - `PUT /api/v1/persons/{id}`: Atualizar dados de uma pessoa
  - `DELETE /api/v1/persons/{id}`: Remover uma pessoa
  - `POST /api/v1/persons/{id}/faces`: Adicionar nova face a uma pessoa
  - `DELETE /api/v1/persons/{id}/faces/{face_id}`: Remover face de uma pessoa
  - `POST /api/v1/persons/recognize`: Reconhecer uma face em imagem base64
  - `POST /api/v1/persons/recognize-file`: Reconhecer uma face em arquivo de imagem

### 2.2. Funcionalidade Futura: Rastreamento de Faces Desconhecidas

#### Visão Geral

Esta funcionalidade permitirá que o sistema detecte, registre e rastreie automaticamente pessoas desconhecidas que aparecem nas câmeras, mesmo antes de serem identificadas manualmente. Isso possibilita o rastreamento retroativo de indivíduos em casos de incidentes de segurança.

#### Benefícios

- Rastreamento contínuo de visitantes desde a primeira aparição
- Histórico completo de aparições mesmo sem identificação manual
- Correlação automática entre diferentes aparições da mesma pessoa
- Capacidade de investigação retroativa após incidentes
- Possibilidade de adicionar identidade posteriormente sem perder o histórico

#### Fluxo de Uso Típico

1. Uma pessoa desconhecida visita o local monitorado (primeira aparição)
2. O sistema detecta a face, extrai características biométricas e cria um perfil "Desconhecido_123"
3. Todas as aparições subsequentes desta pessoa são vinculadas ao mesmo perfil
4. Se a pessoa cometer um delito (em qualquer visita), o operador pode:
   - Consultar o histórico completo de visitas
   - Ver todas as câmeras onde a pessoa apareceu
   - Verificar horários e datas de todas as aparições
5. O operador pode então atribuir uma identidade real à pessoa (ex: "João Silva")

#### Implementação Técnica

##### 1. Modificações no VideoProcessor

```python
def _process_face_recognition(self, frame: np.ndarray, db: Session):
    # Código existente...
    
    for face_location in face_locations:
        # Obter encoding e tentar reconhecer
        face_encoding = face_recognition.face_encodings(rgb_frame, [face_location])[0]
        face_match_result = self._recognize_face_encoding(face_encoding, db)
        
        if face_match_result:
            # Pessoa conhecida - código existente...
            pass
        else:
            # Face desconhecida detectada
            unknown_face = {
                "bbox": face_location,
                "encoding": face_encoding.tolist()
            }
            self._register_unknown_person(frame, unknown_face, db)

def _register_unknown_person(self, frame: np.ndarray, unknown_face: Dict, db: Session):
    """Registra uma pessoa desconhecida no sistema"""
    # Verificar se já não processamos esta câmera recentemente
    now = datetime.now()
    last_unknown_check = getattr(self, "_last_unknown_check", datetime.min)
    
    # Limitar registros para no máximo 1 a cada 5 minutos por câmera
    if (now - last_unknown_check).total_seconds() < 300:
        return
        
    self._last_unknown_check = now
    
    # Criar snapshot
    x1, y1, x2, y2 = unknown_face["bbox"]
    crop = frame[y1:y2, x1:x2]
    
    # Salvar imagem cropada
    face_id = str(uuid.uuid4())
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    filename = f"unknown_{timestamp}_{face_id}.jpg"
    
    snapshot_dir = Path("app/static/faces/unknown")
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    
    face_path = snapshot_dir / filename
    cv2.imwrite(str(face_path), crop)
    
    # Registrar no banco
    from ..crud.person import register_unknown_person
    register_unknown_person(
        db, 
        unknown_face["encoding"], 
        f"faces/unknown/{filename}",
        self.camera_id,
        f"camera_{self.camera_id}"
    )
    
    # Criar evento
    self._create_unknown_person_event(frame, unknown_face, face_id, db)
```

##### 2. Banco de Dados

```sql
-- Tabela para pessoas desconhecidas
CREATE TABLE unknown_persons (
    id TEXT PRIMARY KEY,
    first_seen_at TIMESTAMP NOT NULL,
    last_seen_at TIMESTAMP NOT NULL,
    face_encoding TEXT NOT NULL,  -- Características biométricas serializadas
    face_count INTEGER DEFAULT 1,
    identified_as TEXT DEFAULT NULL,  -- ID da pessoa após identificação
    user_id TEXT NOT NULL,  -- Usuário proprietário
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

-- Tabela para aparições de pessoas desconhecidas
CREATE TABLE unknown_person_appearances (
    id TEXT PRIMARY KEY,
    unknown_person_id TEXT NOT NULL,
    camera_id INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    confidence REAL NOT NULL,
    snapshot_path TEXT NOT NULL,
    bounding_box TEXT NOT NULL,  -- Coordenadas da face na imagem
    FOREIGN KEY(unknown_person_id) REFERENCES unknown_persons(id)
);
```

##### 3. Novos Endpoints da API

```
GET /api/v1/unknown-persons
    Listar pessoas desconhecidas com filtros (data, câmera, etc.)

GET /api/v1/unknown-persons/{id}
    Obter detalhes de uma pessoa desconhecida específica

GET /api/v1/unknown-persons/{id}/appearances
    Listar todas as aparições de uma pessoa desconhecida

PUT /api/v1/unknown-persons/{id}/identify
    Vincular uma pessoa desconhecida a uma pessoa identificada
```

##### 4. Interface de Usuário

Adicionar novas seções na interface:

- **Lista de Pessoas Desconhecidas**:
  - Cards com thumbnail da melhor imagem facial
  - Informações de primeira e última aparição
  - Número total de aparições
  - Botões para ver detalhes e identificar

- **Página de Detalhes**:
  - Timeline de aparições com snapshots
  - Mapa de calor com locais (câmeras) frequentes
  - Estatísticas de horários de atividade
  - Formulário para identificação

#### Estimativa de Implementação

- **Backend**: 3-4 dias de desenvolvimento
- **Frontend**: 2-3 dias de desenvolvimento
- **Testes e otimizações**: 1-2 dias
- **Total**: 6-9 dias de desenvolvimento

## 3. Outra Funcionalidade Futura: Visualização de Gravações Passadas

Implementação de funcionalidade para:

- Armazenar gravações de vídeo por períodos configuráveis
- Visualizar gravações de datas/horários específicos
- Pesquisar e filtrar gravações com base em eventos detectados
- Exportar clipes específicos

## 4. Integração com Roboflow

- Acesso a modelos pré-treinados para diferentes casos de uso
- Possibilidade de treinar modelos customizados para necessidades específicas
- API simplificada para inferência

## 5. Considerações Técnicas

### 5.1 Desempenho

- **Problema**: Alto consumo de CPU/RAM com muitas câmeras
- **Solução**: Implementar processamento em lotes, ajustar intervalo de análise, utilizar resolução mais baixa para processamento

### 5.2 Armazenamento

- **Problema**: Crescimento rápido do uso de disco
- **Solução**: Implementar políticas de retenção, compressão de imagens, armazenamento seletivo baseado em eventos

### 5.3 Privacidade e Segurança

- **Problema**: Dados sensíveis de reconhecimento facial
- **Solução**: Implementar controles de acesso granulares, criptografia de dados, políticas de retenção 