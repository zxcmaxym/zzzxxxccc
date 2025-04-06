import { createContext } from 'react';

const AuthContext = createContext({
  auth: {
    isAuthenticated: false,
    username: '',
    role: null,
  },
  login: () => {},
  logout: () => {},
});

export default AuthContext; 