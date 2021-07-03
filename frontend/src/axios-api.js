import axios from 'axios'


const getAPI = axios.create({
    baseURL: "https://"+ "app.uurnik.com" + "/api/"
})

getAPI.interceptors.request.use(function (config) {
    const token = localStorage.getItem('UserToken');
    config.headers.Authorization = `Bearer ${token}`;
    return config;
  });

export { getAPI }
