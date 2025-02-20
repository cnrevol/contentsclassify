import { Routes, Route } from 'react-router-dom';
import MainLayout from '../layouts/MainLayout';
import Dashboard from '../pages/Dashboard';
import EmailClassifier from '../pages/EmailClassifier';
import FileList from '../pages/FileList';
import TextInput from '../pages/TextInput';
import CategoryGroups from '../pages/CategoryGroups';
// ... other imports

const AppRouter = () => {
  return (
    <Routes>
      <Route path="/" element={<MainLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="email-classifier" element={<EmailClassifier />} />
        <Route path="files" element={<FileList />} />
        <Route path="text" element={<TextInput />} />
        <Route path="categories" element={<CategoryGroups />} />
      </Route>
    </Routes>
  );
};

export default AppRouter;