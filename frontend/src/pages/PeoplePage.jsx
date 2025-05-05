import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaPlus, FaUser, FaUsers, FaEdit, FaTrash, FaCamera, FaUserPlus, FaSearch, FaEye } from 'react-icons/fa';
import Lottie from 'lottie-react';
import api from '../services/api';
import { toast } from 'react-hot-toast';

// Placeholder para animação Lottie (substitua pelo JSON real ou URL)
import instructionAnimation from '../assets/lottie/face-detection.json'; // Você precisará adicionar este arquivo ou usar uma URL

const PeoplePage = () => {
  const navigate = useNavigate();
  const [people, setPeople] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedPerson, setSelectedPerson] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [modalType, setModalType] = useState('add'); // 'add', 'edit', 'addFace'
  const [showInstructionsModal, setShowInstructionsModal] = useState(false);
  const [showWebcamModal, setShowWebcamModal] = useState(false); // Estado para o modal da webcam
  const [showPersonDetailModal, setShowPersonDetailModal] = useState(false);
  const [selectedPersonForDetail, setSelectedPersonForDetail] = useState(null);
  const [personEvents, setPersonEvents] = useState([]);
  const [loadingPersonEvents, setLoadingPersonEvents] = useState(false);

  // Estados para o formulário
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    category: 'default',
    face_image: null,
    class_group: '' // Novo campo para classe/turma
  });

  // Referência para o input de arquivo e vídeo
  const fileInputRef = useRef(null);
  const videoRef = useRef(null); // Ref para o elemento <video>

  // Estado para imagem capturada da webcam
  const [captureMode, setCaptureMode] = useState(false);
  const [previewImage, setPreviewImage] = useState(null);
  const [stream, setStream] = useState(null);

  // Verificar se as instruções já foram vistas ao montar
  useEffect(() => {
    const instructionsAlreadyViewed = localStorage.getItem('peopleInstructionsViewed');
    if (!instructionsAlreadyViewed) {
      setShowInstructionsModal(true);
    }
    fetchPeople();
  }, []);

  // Função para fechar o modal de instruções e marcar como visto
  const handleCloseInstructions = () => {
    localStorage.setItem('peopleInstructionsViewed', 'true');
    setShowInstructionsModal(false);
  };

  // Função para carregar a lista de pessoas
  const fetchPeople = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get('/api/persons/');
      setPeople(response.data || []);
    } catch (err) {
      console.error('Erro ao buscar pessoas:', err);
      setError('Falha ao carregar pessoas cadastradas. Por favor, tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  // Filtrar pessoas com base na pesquisa
  const filteredPeople = people.filter(person =>
    person.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (person.description && person.description.toLowerCase().includes(searchTerm.toLowerCase())) ||
    (person.category && person.category.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  // Manipular arquivo selecionado
  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      setPreviewImage(e.target.result);
      setFormData(prev => ({
        ...prev,
        face_image: e.target.result
      }));
    };
    reader.readAsDataURL(file);
  };

  // Abrir modal para adicionar pessoa
  const openAddModal = () => {
    setModalType('add');
    setFormData({
      name: '',
      description: '',
      category: 'default',
      face_image: null,
      class_group: '' // Limpar ao adicionar
    });
    setPreviewImage(null);
    setShowModal(true);
  };

  // Abrir modal para editar pessoa
  const openEditModal = (person) => {
    setModalType('edit');
    setSelectedPerson(person);
    setFormData({
      name: person.name,
      description: person.description || '',
      category: person.category || 'default',
      class_group: person.class_group || '' // Preencher se existir (precisa vir do backend)
    });
    // Não limpar face_image ou preview ao editar (a menos que queira permitir troca de imagem aqui)
    setShowModal(true);
  };

  // Abrir modal para adicionar face
  const openAddFaceModal = (person) => {
    setModalType('addFace');
    setSelectedPerson(person);
    setPreviewImage(null);
    setFormData(prev => ({
      ...prev,
      face_image: null,
      label: '',
      // Manter outros dados da pessoa (name, desc, cat) se necessário, mas não estão no form addFace
    }));
    setShowModal(true);
  };

  // Manipular alterações no formulário
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // Efeito para associar o stream ao vídeo quando o modal da webcam estiver visível
  useEffect(() => {
    if (showWebcamModal && stream && videoRef.current) {
      videoRef.current.srcObject = stream;
      console.log("Stream da webcam associado via useEffect (no modal dedicado).");
    } else {
      // Não é um erro se o modal não estiver visível
      // console.log("Condições não atendidas para associar stream:", { showWebcamModal, streamExists: !!stream, videoRefExists: !!videoRef.current });
    }
  }, [stream, showWebcamModal]); // Depender do estado do modal da webcam

  // Iniciar captura da webcam e abrir modal dedicado
  const startCaptureAndOpenModal = async () => {
    try {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
        setStream(null); 
      }
      const mediaStream = await navigator.mediaDevices.getUserMedia({ video: true });
      setStream(mediaStream);
      setPreviewImage(null); // Limpar preview antigo
      setShowWebcamModal(true); // Abrir o modal da webcam
    } catch (err) {
      console.error('Erro ao acessar webcam:', err);
      alert('Não foi possível acessar a webcam: ' + err.message);
      setShowWebcamModal(false); // Garantir que o modal não abra se falhar
    }
  };

  // Função chamada pelo botão Capturar NO MODAL DA WEBCAM
  const handleCaptureImageAndCloseModal = () => {
    captureImage(); // Apenas captura e define estado
    stopCapture(); // Para o stream explicitamente aqui
    setShowWebcamModal(false); // Fecha o modal da webcam
  };

  // Função chamada pelo botão Cancelar NO MODAL DA WEBCAM
  const handleCancelCaptureAndCloseModal = () => {
    stopCapture(); // Para o stream
    setShowWebcamModal(false); // Fecha o modal da webcam
  };

  // Parar captura da webcam
  const stopCapture = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
    // Remover setCaptureMode(false) - não usamos mais esse estado diretamente
    // setCaptureMode(false);
  };

  // Capturar imagem da webcam
  const captureImage = () => {
    const video = videoRef.current;
    if (!video) return;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const imgUrl = canvas.toDataURL('image/jpeg');
    setPreviewImage(imgUrl);
    setFormData(prev => ({
      ...prev,
      face_image: imgUrl
    }));
    // REMOVER a chamada stopCapture() daqui
    // stopCapture();
  };

  // Enviar formulário
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.face_image && (modalType === 'add' || modalType === 'addFace')) {
        alert('Por favor, forneça uma imagem facial.');
        return;
    }


    setLoading(true);
    setError(null);

    try {
      let response;
      let payload; // Definir payload fora dos ifs

      if (modalType === 'add') {
        // Adicionar nova pessoa
        payload = { ...formData }; // Copiar formData
        if (formData.category !== 'aluno') {
          delete payload.class_group; // Remover se não for aluno
        }
        response = await api.post('/api/persons/', payload);
        toast.success('Pessoa cadastrada com sucesso!');
      } else if (modalType === 'edit') {
        // Atualizar pessoa existente
        const { name, description, category, class_group } = formData; // Incluir class_group
        payload = { name, description, category };
        if (category === 'aluno') {
          payload.class_group = class_group || ''; // Incluir se for aluno
        }
        // Nota: PUT não envia imagem aqui. Adição de faces é separada.
        response = await api.put(`/api/persons/${selectedPerson.id}`, payload);
        toast.success('Pessoa atualizada com sucesso!');
      } else if (modalType === 'addFace') {
        // Adicionar face a pessoa existente
        // Garantir que apenas os campos necessários para addFace sejam enviados
        payload = {
          person_id: selectedPerson.id,
          face_image: formData.face_image,
          label: formData.label || undefined
        };
        response = await api.post(`/api/persons/${selectedPerson.id}/faces`, payload);
        toast.success('Face adicionada com sucesso!');
      }

      // Fechar modal e recarregar lista
      setShowModal(false);
      fetchPeople();

    } catch (err) {
      console.error('Erro ao salvar dados:', err);
      const errorMsg = err.response?.data?.detail || 'Falha ao salvar. Por favor, tente novamente.';
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  // Remover pessoa
  const handleDelete = async (personId) => {
    if (!window.confirm('Tem certeza que deseja excluir esta pessoa?')) {
      return;
    }

    try {
      setLoading(true);
      await api.delete(`/api/persons/${personId}`);
      toast.success('Pessoa excluída com sucesso');
      fetchPeople();
    } catch (err) {
      console.error('Erro ao excluir pessoa:', err);
      toast.error('Falha ao excluir pessoa');
    } finally {
      setLoading(false);
    }
  };

  // Cleanup ao desmontar componente
  useEffect(() => {
    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, [stream]);

  // Função para ABRIR o modal de detalhes da pessoa
  const openPersonDetailModal = (person) => {
    setSelectedPersonForDetail(person); // Guarda a pessoa selecionada
    setShowPersonDetailModal(true); // Abre o modal
    setPersonEvents([]); // Limpa eventos anteriores
  };

  // Função para FECHAR o modal de detalhes da pessoa
  const closePersonDetailModal = () => {
    setShowPersonDetailModal(false);
    setSelectedPersonForDetail(null);
    setPersonEvents([]);
  };

  // useEffect para buscar eventos quando o modal de detalhes abrir
  useEffect(() => {
    const fetchPersonEvents = async () => {
      if (selectedPersonForDetail) {
        setLoadingPersonEvents(true);
        try {
          const response = await api.get(`/api/persons/${selectedPersonForDetail.id}/events`);
          setPersonEvents(response.data || []);
        } catch (err) {
          console.error('Erro ao buscar eventos da pessoa:', err);
          toast.error("Falha ao buscar eventos associados.");
        }
        setLoadingPersonEvents(false);
      }
    };

    if (showPersonDetailModal) {
      fetchPersonEvents();
    }
  }, [showPersonDetailModal, selectedPersonForDetail]);

  // Função auxiliar para formatar data/hora (pode mover para utils se usar em mais lugares)
  const formatDateTime = (dateTimeStr) => {
    if (!dateTimeStr) return 'N/A';
    try {
        const date = new Date(dateTimeStr);
        return date.toLocaleString('pt-BR', {
            day: '2-digit', month: '2-digit', year: 'numeric',
            hour: '2-digit', minute: '2-digit'
        });
    } catch (e) {
        return 'Data inválida';
    }
  };

  return (
    <div className="container mx-auto px-4 py-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Pessoas Cadastradas</h1>
        <button
          onClick={openAddModal}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md flex items-center"
        >
          <FaPlus className="mr-2" /> Adicionar Pessoa
        </button>
      </div>

      {/* Barra de pesquisa */}
      <div className="mb-6">
        <div className="relative">
          <input
            type="text"
            placeholder="Buscar pessoas..."
            className="w-full max-w-lg px-4 py-2 border rounded-md pl-10 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <FaSearch className="absolute left-3 top-3 text-gray-400" />
        </div>
      </div>

      {/* Mensagem de carregamento */}
      {loading && !people.length && ( // Mostrar loading inicial apenas se não houver pessoas
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
          <span className="ml-2 text-gray-600 dark:text-gray-400">Carregando...</span>
        </div>
      )}

      {/* Mensagem de erro */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {/* Lista de pessoas */}
      {!loading && !error && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredPeople.length === 0 ? (
            <div className="col-span-1 md:col-span-2 lg:col-span-3 text-center py-8">
              <div className="flex flex-col items-center justify-center text-gray-500 dark:text-gray-400">
                <FaUsers className="text-5xl mb-4" />
                <p>Nenhuma pessoa encontrada.</p>
                <button
                  onClick={openAddModal}
                  className="mt-4 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md flex items-center"
                >
                  <FaUserPlus className="mr-2" /> Adicionar Pessoa
                </button>
              </div>
            </div>
          ) : (
            filteredPeople.map((person) => (
              <div key={person.id} className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden flex items-center p-4 space-x-4">
                {/* Imagem Redonda à Esquerda */}
                <div className="flex-shrink-0">
                  {person.thumbnail_url ? (
                    <img
                      src={person.thumbnail_url}
                      alt={person.name}
                      className="w-20 h-20 rounded-full object-cover border-2 border-gray-300 dark:border-gray-600"
                      // Adicionar onError para fallback se a imagem quebrar
                      onError={(e) => { e.target.onerror = null; e.target.src = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0iY3VycmVudENvbG9yIiBjbGFzcz0idy02IGgtNiI+CiAgPHBhdGggZmlsbC1ydWxlPSJldmVub2RkIiBkPSJNMTguNjU3IDE2LjgzYS43NS43NSAwIDEwLTEuMDUtMS4wNmwtMS4zIDMuOTA3YS43NS43NSAwIDAxLTEuNDIuMDQyTDEyLjY4IDE0LjJhLjUuNSAwIDAwLS44MjYuMjE3bC0xLjMzOCAzLjM0M2EuNS41IDAgMDEtLjg2NS4wNWwtMS4zMjUtMi42NTEtMS41NjggMS41NjdBLjc1Ljc1IDAgMTE3LjM5MiAxNC42MmwxLjM3OC0xLjM3OGEuNzUuNzUgMCAwMTIuMjA2IDBsMi42NjcgMi42NjdjLjc5NC43OTUgMS43MjIuOTI3IDIuNTU0Ljg0MmE0LjUgNC41IDAgMDAyLjQ0OC0uODQyem0zLjI4OC02LjUxMmEzIDMgMCAxMC02IDAgMyAzIDAgMDA2IDB6bS04LjgxNSA5LjA2N2EuNzUuNzUgMCAwMC0uMDguMjVsLjAwMS0uMDAxLjAxMS0uMDAxYS43NS43NSAwIDAwLjA4LS4yNDl6IiBjbGlwLXJ1bGU9ImV2ZW5vZGQiIC8+Cjwvc3ZnPg==' }} // Placeholder SVG simples
                    />
                  ) : (
                    <div className="w-20 h-20 rounded-full flex items-center justify-center bg-gray-200 dark:bg-gray-700 border-2 border-gray-300 dark:border-gray-600">
                      <FaUser className="text-4xl text-gray-400 dark:text-gray-500" />
                    </div>
                  )}
                </div>

                {/* Conteúdo à Direita */}
                <div className="flex-1 min-w-0">
                  <div onClick={() => openPersonDetailModal(person)} className="cursor-pointer group">
                    <div className="flex justify-between items-start mb-1">
                      <h2 className="text-lg font-semibold text-gray-900 dark:text-white truncate group-hover:text-blue-600 dark:group-hover:text-blue-400" title={person.name}>{person.name}</h2>
                      <span className="flex-shrink-0 ml-2 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-2 py-0.5 rounded-full text-xs font-medium">
                        {person.category || 'default'}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-2 truncate group-hover:text-blue-600 dark:group-hover:text-blue-400" title={person.description}>
                      {person.description || "Sem descrição"}
                    </p>
                    {/* Exibir Classe/Turma se for aluno */}
                    {person.category === 'aluno' && person.class_group && (
                      <p className="text-sm text-indigo-600 dark:text-indigo-400 mb-2 truncate font-medium" title={person.class_group}>
                        Turma: {person.class_group}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center text-xs text-gray-500 dark:text-gray-400 mb-3">
                    <FaUser className="mr-1" />
                    <span>{person.face_count} {person.face_count === 1 ? 'face' : 'faces'}</span>
                  </div>
                  <div className="flex justify-start space-x-2">
                    <button
                      onClick={() => openPersonDetailModal(person)}
                      className="p-1.5 text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600"
                      title="Ver Eventos"
                    >
                      <FaEye size={14}/>
                    </button>
                    <button
                      onClick={() => openEditModal(person)}
                      className="p-1.5 text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600"
                      title="Editar"
                    >
                      <FaEdit size={14}/>
                    </button>
                    <button
                      onClick={() => handleDelete(person.id)}
                      className="p-1.5 text-red-500 dark:text-red-400 bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600"
                      title="Remover"
                    >
                      <FaTrash size={14}/>
                    </button>
                    <button
                      onClick={() => openAddFaceModal(person)}
                      className="p-1.5 text-blue-600 dark:text-blue-400 bg-blue-100 dark:bg-gray-700 rounded-md hover:bg-blue-200 dark:hover:bg-gray-600"
                      title="Adicionar face"
                    >
                      <FaCamera size={14}/>
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Modal Adicionar/Editar/AddFace */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm">
          <div className="bg-white/80 dark:bg-gray-800/60 rounded-lg w-full max-w-md mx-4 p-6 shadow-lg">
            <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">
              {modalType === 'add' && 'Adicionar Pessoa'}
              {modalType === 'edit' && 'Editar Pessoa'}
              {modalType === 'addFace' && `Adicionar Face para ${selectedPerson?.name}`}
            </h2>

            <form onSubmit={handleSubmit}>
              {/* Campos comuns para add e edit */}
              {(modalType === 'add' || modalType === 'edit') && (
                <>
                  <div className="mb-4">
                    <label className="block text-sm font-medium mb-1 dark:text-gray-300">Nome</label>
                    <input
                      type="text"
                      name="name"
                      value={formData.name}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                      required
                    />
                  </div>

                  <div className="mb-4">
                    <label className="block text-sm font-medium mb-1 dark:text-gray-300">Descrição</label>
                    <textarea
                      name="description"
                      value={formData.description}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border rounded-md h-20 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                    />
                  </div>

                  <div className="mb-4">
                    <label className="block text-sm font-medium mb-1 dark:text-gray-300">Categoria</label>
                    <select
                      name="category"
                      value={formData.category}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                    >
                      <option value="default">Padrão</option>
                      <option value="aluno">Aluno</option> {/* Adicionar opção Aluno */}
                      <option value="employee">Funcionário</option>
                      <option value="visitor">Visitante</option>
                      <option value="vip">VIP</option>
                      <option value="restricted">Acesso Restrito</option>
                    </select>
                  </div>

                  {/* Input Condicional para Classe/Turma */}
                  {formData.category === 'aluno' && (
                    <div className="mb-4">
                      <label className="block text-sm font-medium mb-1 dark:text-gray-300">Classe/Turma</label>
                      <input
                        type="text"
                        name="class_group"
                        value={formData.class_group || ''}
                        onChange={handleInputChange}
                        className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                        placeholder="Ex: 3º Ano B"
                      />
                    </div>
                  )}
                </>
              )}

              {/* Campo de rótulo para add face */}
              {modalType === 'addFace' && (
                <div className="mb-4">
                  <label className="block text-sm font-medium mb-1 dark:text-gray-300">Rótulo (opcional)</label>
                  <input
                    type="text"
                    name="label"
                    value={formData.label || ''}
                    onChange={handleInputChange}
                    placeholder="Ex: perfil, com óculos, etc."
                    className="w-full px-3 py-2 border rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                  />
                </div>
              )}

              {/* Upload de imagem (agora sem a preview da câmera aqui) */}
              {(modalType === 'add' || modalType === 'addFace') && (
                <div className="mb-4">
                  <label className="block text-sm font-medium mb-1 dark:text-gray-300">Imagem Facial</label>

                  {/* Preview da imagem CAPTURADA ou do ARQUIVO */}
                  {previewImage && (
                    <div className="mb-2 relative">
                      <img
                        src={previewImage}
                        alt="Preview"
                        className="w-full h-48 object-cover rounded-md"
                      />
                      <button
                        type="button"
                        onClick={() => {
                          setPreviewImage(null);
                          setFormData(prev => ({
                            ...prev,
                            face_image: null
                          }));
                        }} // Botão para limpar a imagem selecionada/capturada
                        className="absolute top-2 right-2 bg-red-600 text-white rounded-full p-1.5 shadow-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
                      >
                        <FaTrash size={14} />
                      </button>
                    </div>
                  )}

                  {/* Botões de upload/captura (só aparecem se não houver preview) */}
                  {!previewImage && (
                    <div className="flex space-x-2">
                      <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        className="bg-blue-600 text-white px-4 py-2 rounded-md flex-1"
                      >
                        Escolher Arquivo
                      </button>
                      <button
                        type="button"
                        onClick={startCaptureAndOpenModal} // Chama a função para ABRIR O MODAL DA WEBCAM
                        className="bg-green-600 text-white px-4 py-2 rounded-md flex-1"
                      >
                        Usar Webcam
                      </button>
                      <input
                        type="file"
                        ref={fileInputRef}
                        onChange={handleFileChange}
                        accept="image/*"
                        className="hidden"
                      />
                    </div>
                  )}
                </div>
              )}

              {/* Botões de ação */}
              <div className="flex justify-end space-x-2 mt-6">
                <button
                  type="button"
                  onClick={() => {
                    setShowModal(false);
                    stopCapture();
                  }}
                  className="px-4 py-2 bg-gray-300 text-gray-800 rounded-md hover:bg-gray-400 dark:bg-gray-600 dark:text-gray-300 dark:hover:bg-gray-500 focus:outline-none focus:ring-2 focus:ring-gray-500"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {modalType === 'add' && 'Adicionar'}
                  {modalType === 'edit' && 'Salvar'}
                  {modalType === 'addFace' && 'Adicionar Face'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* NOVO Modal Dedicado para Captura da Webcam */}
      {showWebcamModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75 backdrop-blur-md"> {/* Fundo mais escuro e blur maior? */}
          <div className="bg-white dark:bg-gray-800 rounded-lg w-full max-w-lg mx-4 p-4 shadow-lg text-center">
             <h3 className="text-lg font-medium mb-3 text-gray-900 dark:text-white">Posicione o Rosto</h3>
              {/* Container da Câmera com Overlay */}
              <div className="mb-4 relative w-full aspect-video mx-auto max-w-md overflow-hidden rounded-md"> {/* Adicionar overflow-hidden e rounded-md aqui */}
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  // Remover rounded-md daqui, aplicar no container pai
                  className="w-full h-full object-cover bg-gray-900"
                ></video>
                {/* Moldura Guia (Overlay) */}
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <div 
                    // Oval mais estreito (w-1/3), Borda tracejada, Sombra branca externa
                    className="w-1/3 h-4/5 border-4 border-dashed border-white/70 rounded-full opacity-80 shadow-[0_0_0_9999px_rgba(255,255,255,0.8)]"
                  >
                  </div>
                </div>
              </div>
               {/* Botões de Capturar / Cancelar específicos deste modal */}
              <div className="flex justify-center space-x-4">
                <button
                  type="button"
                  onClick={handleCaptureImageAndCloseModal} // Captura e fecha ESTE modal
                  className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500"
                >
                  Capturar
                </button>
                <button
                  type="button"
                  onClick={handleCancelCaptureAndCloseModal} // Cancela e fecha ESTE modal
                  className="px-6 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
                >
                  Cancelar
                </button>
              </div>
          </div>
        </div>
      )}

      {/* Modal de Instruções */}
      {showInstructionsModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm">
          <div className="bg-white/80 dark:bg-gray-800/80 rounded-lg w-full max-w-lg mx-4 p-6 shadow-lg text-center">
            <h2 className="text-2xl font-bold mb-4 text-gray-900 dark:text-white">
              Como cadastrar uma pessoa
            </h2>

            <div className="w-52 mx-auto"> {/* Ajuste tamanho conforme necessário */}
              <Lottie animationData={instructionAnimation} loop={true} />
            </div>

            <div className="text-left mb-6 space-y-2">
              <p className="text-gray-800 dark:text-gray-200">Para cadastrar uma pessoa, siga estas dicas:</p>
              <ul className="list-disc list-inside ml-4 text-gray-700 dark:text-gray-100 space-y-1">
                <li><strong className="text-blue-600 dark:text-blue-400 font-semibold">Iluminação:</strong> Use luz frontal e evite sombras fortes no rosto. Luz natural suave é ideal.</li>
                <li><strong className="text-blue-600 dark:text-blue-400 font-semibold">Fundo:</strong> Prefira um fundo neutro e claro, sem muitas distrações.</li>
                <li><strong className="text-blue-600 dark:text-blue-400 font-semibold">Ângulo:</strong> Olhe diretamente para a câmera. Evite fotos de perfil ou com a cabeça muito inclinada.</li>
                <li><strong className="text-blue-600 dark:text-blue-400 font-semibold">Expressão:</strong> Mantenha uma expressão neutra, sem sorrir muito ou fazer caretas.</li>
                <li><strong className="text-blue-600 dark:text-blue-400 font-semibold">Acessórios:</strong> Evite chapéus ou óculos escuros. Se usar óculos de grau normalmente, pode mantê-los, mas certifique-se de que não há reflexos.</li>
                <li><strong className="text-blue-600 dark:text-blue-400 font-semibold">Qualidade:</strong> Use uma imagem nítida e focada.</li>
              </ul>
            </div>

            <button
              type="button"
              onClick={handleCloseInstructions}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              Entendi
            </button>
          </div>
        </div>
      )}

      {/* NOVO Modal Detalhes da Pessoa e Eventos */}
      {showPersonDetailModal && selectedPersonForDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75 backdrop-blur-md">
          <div className="bg-white dark:bg-gray-800 rounded-lg w-full max-w-2xl mx-4 max-h-[80vh] flex flex-col shadow-lg">
            {/* Cabeçalho do Modal */}
            <div className="flex justify-between items-center p-4 border-b border-gray-300 dark:border-gray-700">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">Detalhes de {selectedPersonForDetail.name}</h2>
              <button onClick={closePersonDetailModal} className="text-gray-500 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-500">&times;</button>
            </div>

            {/* Conteúdo Rolável */}
            <div className="p-6 overflow-y-auto flex-1">
              {/* Informações da Pessoa */}
              <div className="mb-6 p-4 bg-gray-100 dark:bg-gray-700 rounded-lg text-center"> {/* Adicionado text-center */}
                 {/* Substituir ID pela Imagem */}
                 <div className="mb-3">
                    {selectedPersonForDetail.thumbnail_url ? (
                        <img
                            src={selectedPersonForDetail.thumbnail_url}
                            alt={selectedPersonForDetail.name}
                            className="w-24 h-24 rounded-full object-cover border-2 border-gray-300 dark:border-gray-600 mx-auto shadow-md"
                            onError={(e) => { e.target.onerror = null; e.target.style.display='none'; /* Esconder se quebrar */ }}
                        />
                    ) : (
                        <div className="w-24 h-24 rounded-full flex items-center justify-center bg-gray-200 dark:bg-gray-600 border-2 border-gray-300 dark:border-gray-600 mx-auto shadow-md">
                            <FaUser className="text-5xl text-gray-400 dark:text-gray-500" />
                        </div>
                    )}
                 </div>
                 {/* <p><span className="font-semibold">ID:</span> {selectedPersonForDetail.id}</p> */}
                 <p className="text-lg font-semibold text-gray-900 dark:text-white">{selectedPersonForDetail.name}</p>
                 <p className="text-sm text-gray-600 dark:text-gray-400">{selectedPersonForDetail.description || 'Sem descrição'}</p>
                 <p className="text-sm"><span className="font-medium">Categoria:</span> {selectedPersonForDetail.category || '-'}</p>
                 {selectedPersonForDetail.category === 'aluno' && 
                    <p className="text-sm"><span className="font-medium">Turma:</span> {selectedPersonForDetail.class_group || '-'}</p>
                 }
                 <p className="text-sm"><span className="font-medium">Faces Cadastradas:</span> {selectedPersonForDetail.face_count}</p>
              </div>

              {/* Lista de Eventos Associados */}
              <h3 className="text-lg font-semibold mb-3 text-gray-900 dark:text-white">Eventos Associados</h3>
              {loadingPersonEvents ? (
                <div className="text-center py-4">Carregando eventos...</div>
              ) : personEvents.length === 0 ? (
                <div className="text-center py-4 text-gray-500 dark:text-gray-400">Nenhum evento encontrado para esta pessoa.</div>
              ) : (
                <ul className="space-y-2">
                  {personEvents.map(event => (
                    <li key={event.id} className="p-3 bg-gray-50 dark:bg-gray-700 rounded flex justify-between items-center text-sm">
                      <div>
                        <span className="font-medium">{formatDateTime(event.timestamp)}</span>
                        <span className="ml-2 text-gray-600 dark:text-gray-300">({event.event_type} - Conf: {(event.confidence * 100).toFixed(0)}%)</span>
                        <span className="ml-2 text-gray-500 dark:text-gray-400">em {event.camera_name || event.camera_id}</span>
                      </div>
                      <button 
                        onClick={() => navigate(`/events/${event.id}`)} // Navega para detalhes do evento
                        className="text-blue-600 dark:text-blue-400 hover:underline text-xs"
                      >
                        Ver Detalhes
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>

             {/* Rodapé do Modal (Opcional) */}
             <div className="p-4 border-t border-gray-300 dark:border-gray-700 flex justify-end">
                <button
                    onClick={closePersonDetailModal}
                    className="px-4 py-2 bg-gray-300 text-gray-800 rounded-md hover:bg-gray-400 dark:bg-gray-600 dark:text-gray-300 dark:hover:bg-gray-500"
                >
                    Fechar
                </button>
             </div>
          </div>
        </div>
      )}

    </div>
  );
};

export default PeoplePage; 