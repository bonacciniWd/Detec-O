import DashboardPage from './pages/DashboardPage';
import CamerasPage from './pages/CamerasPage';
import CameraSettings from './pages/CameraSettings';
import EventsPage from './pages/EventsPage'; 
import CameraDashboard from './pages/CameraDashboard';
import EventDetail from './pages/EventDetail';
import PeoplePage from './pages/PeoplePage';

const AppRoutes = () => {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route element={<PrivateRoute />}>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="cameras" element={<CamerasPage />} />
          <Route path="cameras/:cameraId" element={<CameraSettings />} />
          <Route path="events" element={<EventsPage />} />
          <Route path="events/:eventId" element={<EventDetail />} />
          <Route path="camera-dashboard" element={<CameraDashboard />} />
          <Route path="people" element={<PeoplePage />} />
          {/* ... existing routes ... */}
        </Route>
      </Route>
    </Routes>
  );
}; 