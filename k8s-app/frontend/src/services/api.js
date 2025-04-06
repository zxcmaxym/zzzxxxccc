import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = {
  // Student endpoints
  studentLogin: async (name) => {
    try {
      const response = await axios.get(`${API_URL}/student`, {
        params: { name }
      });
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.response?.data || 'Failed to login' };
    }
  },
  
  getStudentTasks: async (name) => {
    try {
      const response = await axios.get(`${API_URL}/student`, {
        params: { name }
      });
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.response?.data || 'Failed to get tasks' };
    }
  },
  
  getTaskDetails: async (taskName, studentName) => {
    try {
      const response = await axios.get(`${API_URL}/student/task/${taskName}`, {
        params: { name: studentName }
      });
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.response?.data || 'Failed to get task details' };
    }
  },
  
  submitTask: async (studentName, taskName, scriptFile) => {
    try {
      const formData = new FormData();
      formData.append('student_name', studentName);
      formData.append('task_name', taskName);
      formData.append('script_file', scriptFile);
      
      const response = await axios.post(`${API_URL}/student/validate`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.response?.data || 'Failed to submit task' };
    }
  },
  
  getTaskResult: async (taskName, studentName) => {
    try {
      const response = await axios.get(`${API_URL}/student/task/result/${taskName}/${studentName}`);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.response?.data || 'Failed to get task result' };
    }
  },
  
  // Teacher endpoints
  teacherLogin: async (name) => {
    try {
      const response = await axios.get(`${API_URL}/teacher`);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.response?.data || 'Failed to login' };
    }
  },
  
  createTask: async (taskName, description, teacherName, groupNames, scriptFile, variablesFile = null, findFile = null) => {
    try {
      const formData = new FormData();
      formData.append('task_name', taskName);
      formData.append('description', description);
      formData.append('teacher_name', teacherName);
      formData.append('group_names', JSON.stringify(groupNames));
      formData.append('script_file', scriptFile);
      
      if (variablesFile) {
        formData.append('variables_file', variablesFile);
      }
      
      if (findFile) {
        formData.append('find_file', findFile);
      }
      
      const response = await axios.post(`${API_URL}/teacher/task/create`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.response?.data || 'Failed to create task' };
    }
  },
  
  deleteTask: async (taskName) => {
    try {
      const response = await axios.delete(`${API_URL}/teacher/task/delete/${taskName}`);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.response?.data || 'Failed to delete task' };
    }
  },
  
  getTaskResults: async (taskName) => {
    try {
      const response = await axios.get(`${API_URL}/teacher/task/results/${taskName}`);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.response?.data || 'Failed to get task results' };
    }
  },
  
  getTeacherInfo: async () => {
    try {
      const response = await axios.get(`${API_URL}/teacher`);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.response?.data || 'Failed to get teacher info' };
    }
  },
  
  createGroup: async (groupName, teacherName) => {
    try {
      const formData = new FormData();
      formData.append('group_name', groupName);
      formData.append('teacher_name', teacherName);
      
      const response = await axios.post(`${API_URL}/teacher/group/create`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.response?.data || 'Failed to create group' };
    }
  },
  
  addStudentToGroup: async (studentName, groupName, teacherName) => {
    try {
      const response = await axios.post(`${API_URL}/teacher/group/add-student`, {
        student_group: {
          student_name: studentName,
          group_name: groupName
        },
        teacher_name: teacherName
      });
      
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.response?.data || 'Failed to add student to group' };
    }
  },
  
  getGroupStudents: async (groupName, teacherName) => {
    try {
      const response = await axios.get(`${API_URL}/teacher/group/${groupName}/students`, {
        params: { teacher_name: teacherName }
      });
      
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.response?.data || 'Failed to get group students' };
    }
  },
  
  getGroupTasks: async (groupName, teacherName) => {
    try {
      const response = await axios.get(`${API_URL}/teacher/group/${groupName}/tasks`, {
        params: { teacher_name: teacherName }
      });
      
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.response?.data || 'Failed to get group tasks' };
    }
  }
};

export default api; 