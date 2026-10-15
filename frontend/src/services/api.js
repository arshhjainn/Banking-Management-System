import axios from 'axios';

export default axios.create({
  // In development Vite proxies /api to Flask. Keeping requests same-origin
  // lets the browser send Flask's session cookie when the UI uses localhost.
  baseURL: import.meta.env.VITE_API_URL || '/api',
  withCredentials: true,
});
