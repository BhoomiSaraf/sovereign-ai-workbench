import { BrowserRouter, Route, Routes } from 'react-router-dom'
import AppShell from './components/AppShell'
import Dashboard from './pages/Dashboard'
import TaskWorkspace from './pages/TaskWorkspace'
import KnowledgeBase from './pages/KnowledgeBase'
import ModelsPage from './pages/ModelsPage'
import ArtifactsPage from './pages/ArtifactsPage'
import SecurityPage from './pages/SecurityPage'

export default function App() {
  return (
    <BrowserRouter>
      <AppShell>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/workspace" element={<TaskWorkspace />} />
          <Route path="/knowledge" element={<KnowledgeBase />} />
          <Route path="/models" element={<ModelsPage />} />
          <Route path="/artifacts" element={<ArtifactsPage />} />
          <Route path="/security" element={<SecurityPage />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  )
}
