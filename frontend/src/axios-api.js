import axios from 'axios'


const getAPI = axios.create({
    baseURL: "http://192.168.100.98:8001/api/"
})


getAPI.interceptors.request.use(function (config) {
    const token = localStorage.getItem('UserToken');
    config.headers.Authorization = `Bearer ${token}`;
    return config;
  });

export { getAPI }
