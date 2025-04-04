import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaPlus, FaUser, FaUsers, FaEdit, FaTrash, FaCamera, FaUserPlus, FaSearch } from 'react-icons/fa';
import api from '../services/api';

const PeoplePage = () => {
  const navigate = useNavigate();
  const [people, setPeople] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedPerson, setSelectedPerson] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [modalType, setModalType] = useState('add'); // 'add', 'edit', 'addFace'
  
  // Estados para o formulário
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    category: 'default',
    face_image: null
  });
  
  // Referência para o input de arquivo
  const fileInputRef = useRef(null);
  
  // Estado para imagem capturada da webcam
  const [captureMode, setCaptureMode] = useState(false);
  const [previewImage, setPreviewImage] = useState(null);
  const videoRef = useRef(null);
  const [stream, setStream] = useState(null);
  
  // Função para carregar a lista de pessoas
  const fetchPeople = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/v1/persons');
      setPeople(response.data.items || []);
    } catch (err) {
      console.error('Erro ao buscar pessoas:', err);
      setError('Não foi possível carregar a lista de pessoas.');
    } finally {
      setLoading(false);
    }
  };
  
  // Carregar lista de pessoas ao montar o componente
  useEffect(() => {
    fetchPeople();
  }, []);
  
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
      face_image: null
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
    });
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
  
  // Iniciar captura da webcam
  const startCapture = async () => {
    try {
      // Parar stream anterior se existir
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
      
      // Solicitar acesso à webcam
      const mediaStream = await navigator.mediaDevices.getUserMedia({ video: true });
      setStream(mediaStream);
      
      // Associar stream ao elemento de vídeo
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
      
      setCaptureMode(true);
    } catch (err) {
      console.error('Erro ao acessar webcam:', err);
      alert('Não foi possível acessar a webcam: ' + err.message);
    }
  };
  
  // Parar captura da webcam
  const stopCapture = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
    setCaptureMode(false);
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
    
    // Parar a captura após obter a imagem
    stopCapture();
  };
  
  // Limpar captura
  const clearCapture = () => {
    setPreviewImage(null);
    setFormData(prev => ({
      ...prev,
      face_image: null
    }));
  };
  
  // Enviar formulário
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.face_image && modalType !== 'edit') {
      alert('Por favor, forneça uma imagem facial.');
      return;
    }
    
    try {
      let response;
      
      if (modalType === 'add') {
        // Adicionar nova pessoa
        response = await api.post('/api/v1/persons', formData);
        alert('Pessoa cadastrada com sucesso!');
      } else if (modalType === 'edit') {
        // Atualizar pessoa existente
        const { name, description, category } = formData;
        response = await api.put(`/api/v1/persons/${selectedPerson.id}`, {
          name,
          description,
          category
        });
        alert('Pessoa atualizada com sucesso!');
      } else if (modalType === 'addFace') {
        // Adicionar face a pessoa existente
        response = await api.post(`/api/v1/persons/${selectedPerson.id}/faces`, {
          person_id: selectedPerson.id,
          face_image: formData.face_image,
          label: formData.label || undefined
        });
        alert('Face adicionada com sucesso!');
      }
      
      // Fechar modal e recarregar lista
      setShowModal(false);
      fetchPeople();
      
    } catch (err) {
      console.error('Erro ao salvar dados:', err);
      alert(`Erro: ${err.response?.data?.detail || err.message}`);
    }
  };
  
  // Remover pessoa
  const handleDelete = async (personId) => {
    if (!confirm('Tem certeza que deseja remover esta pessoa?')) {
      return;
    }
    
    try {
      await api.delete(`/api/v1/persons/${personId}`);
      alert('Pessoa removida com sucesso!');
      fetchPeople();
    } catch (err) {
      console.error('Erro ao remover pessoa:', err);
      alert(`Erro: ${err.response?.data?.detail || err.message}`);
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
  
  return (
    <div className="container mx-auto px-4 py-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Pessoas Cadastradas</h1>
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
            className="w-full px-4 py-2 border rounded-md pl-10"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <FaSearch className="absolute left-3 top-3 text-gray-400" />
        </div>
      </div>
      
      {/* Mensagem de carregamento */}
      {loading && (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
          <span className="ml-2">Carregando...</span>
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
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {filteredPeople.length === 0 ? (
            <div className="col-span-full text-center py-8">
              <div className="flex flex-col items-center justify-center text-gray-500">
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
              <div key={person.id} className="bg-white rounded-lg shadow-md overflow-hidden">
                <div className="h-48 overflow-hidden relative">
                  {person.thumbnail_url ? (
                    <img
                      src={person.thumbnail_url}
                      alt={person.name}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center bg-gray-200">
                      <FaUser className="text-5xl text-gray-400" />
                    </div>
                  )}
                  <div className="absolute top-2 right-2 bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs">
                    {person.category}
                  </div>
                </div>
                <div className="p-4">
                  <h2 className="text-xl font-semibold mb-1">{person.name}</h2>
                  <p className="text-sm text-gray-600 mb-2 h-10 overflow-hidden">
                    {person.description || "Sem descrição"}
                  </p>
                  <div className="flex items-center text-sm text-gray-500 mb-4">
                    <FaUser className="mr-1" />
                    <span>{person.face_count} {person.face_count === 1 ? 'face' : 'faces'}</span>
                  </div>
                  <div className="flex justify-between">
                    <div className="flex space-x-2">
                      <button
                        onClick={() => openEditModal(person)}
                        className="p-2 bg-gray-100 rounded-md hover:bg-gray-200"
                        title="Editar"
                      >
                        <FaEdit />
                      </button>
                      <button
                        onClick={() => handleDelete(person.id)}
                        className="p-2 bg-gray-100 rounded-md hover:bg-gray-200 text-red-500"
                        title="Remover"
                      >
                        <FaTrash />
                      </button>
                    </div>
                    <button
                      onClick={() => openAddFaceModal(person)}
                      className="p-2 bg-blue-100 rounded-md hover:bg-blue-200 text-blue-800 flex items-center"
                      title="Adicionar face"
                    >
                      <FaCamera className="mr-1" />
                      <span>Add Face</span>
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
      
      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-lg w-full max-w-md mx-4 p-6">
            <h2 className="text-xl font-bold mb-4">
              {modalType === 'add' && 'Adicionar Pessoa'}
              {modalType === 'edit' && 'Editar Pessoa'}
              {modalType === 'addFace' && `Adicionar Face para ${selectedPerson?.name}`}
            </h2>
            
            <form onSubmit={handleSubmit}>
              {/* Campos comuns para add e edit */}
              {(modalType === 'add' || modalType === 'edit') && (
                <>
                  <div className="mb-4">
                    <label className="block text-sm font-medium mb-1">Nome</label>
                    <input
                      type="text"
                      name="name"
                      value={formData.name}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border rounded-md"
                      required
                    />
                  </div>
                  
                  <div className="mb-4">
                    <label className="block text-sm font-medium mb-1">Descrição</label>
                    <textarea
                      name="description"
                      value={formData.description}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border rounded-md h-20"
                    />
                  </div>
                  
                  <div className="mb-4">
                    <label className="block text-sm font-medium mb-1">Categoria</label>
                    <select
                      name="category"
                      value={formData.category}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border rounded-md"
                    >
                      <option value="default">Padrão</option>
                      <option value="employee">Funcionário</option>
                      <option value="visitor">Visitante</option>
                      <option value="vip">VIP</option>
                      <option value="restricted">Acesso Restrito</option>
                    </select>
                  </div>
                </>
              )}
              
              {/* Campo de rótulo para add face */}
              {modalType === 'addFace' && (
                <div className="mb-4">
                  <label className="block text-sm font-medium mb-1">Rótulo (opcional)</label>
                  <input
                    type="text"
                    name="label"
                    value={formData.label || ''}
                    onChange={handleInputChange}
                    placeholder="Ex: perfil, com óculos, etc."
                    className="w-full px-3 py-2 border rounded-md"
                  />
                </div>
              )}
              
              {/* Upload de imagem */}
              {(modalType === 'add' || modalType === 'addFace') && (
                <div className="mb-4">
                  <label className="block text-sm font-medium mb-1">Imagem Facial</label>
                  
                  {/* Preview da imagem */}
                  {previewImage && (
                    <div className="mb-2 relative">
                      <img 
                        src={previewImage} 
                        alt="Preview" 
                        className="w-full h-48 object-cover rounded-md"
                      />
                      <button
                        type="button"
                        onClick={clearCapture}
                        className="absolute top-2 right-2 bg-red-600 text-white rounded-full p-1"
                      >
                        <FaTrash size={14} />
                      </button>
                    </div>
                  )}
                  
                  {/* Modo de captura */}
                  {captureMode && (
                    <div className="mb-2">
                      <video
                        ref={videoRef}
                        autoPlay
                        muted
                        className="w-full h-48 object-cover rounded-md"
                      ></video>
                      <div className="flex justify-center mt-2">
                        <button
                          type="button"
                          onClick={captureImage}
                          className="bg-green-600 text-white px-4 py-2 rounded-md mr-2"
                        >
                          Capturar
                        </button>
                        <button
                          type="button"
                          onClick={stopCapture}
                          className="bg-red-600 text-white px-4 py-2 rounded-md"
                        >
                          Cancelar
                        </button>
                      </div>
                    </div>
                  )}
                  
                  {/* Botões de upload/captura */}
                  {!captureMode && !previewImage && (
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
                        onClick={startCapture}
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
                  className="px-4 py-2 border rounded-md"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
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
    </div>
  );
};

export default PeoplePage; 