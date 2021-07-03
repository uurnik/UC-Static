import axios from 'axios'


const getAPI = axios.create({
    baseURL: "http://"+ process.env.VUE_APP_DOMAIN_NAME + "/api/"
})

getAPI.interceptors.request.use(function (config) {
    const token = localStorage.getItem('UserToken');
    config.headers.Authorization = `Bearer ${token}`;
    return config;
  });

export { getAPI }
