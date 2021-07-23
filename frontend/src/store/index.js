import Vue from 'vue'
import Vuex from 'vuex'
import { getAPI } from '../axios-api.js'


Vue.use(Vuex)
export default new Vuex.Store({
    state: {
        menuDialogs: {
            1: false,
            2: false,
            3: false,
        },
        copp: false,
        devicehardening: false,
        notConfigured: true,
        accessType: null,
        accessToken: null,
        refreshToken: null,
        APIData: '',
        accesstype: null,
        dns: null,
        toggleloader:false,
        hidestatusbtn: true,
        showstatustable4: false,
        showtasks4: false,
        devices: [],
        e1:1,
    },
    mutations: {
        updateStorage(state, { access, refresh }) {
            state.accessToken = access
            state.refreshToken = refresh
            localStorage.setItem('UserToken', access)

        },
        destroyToken(state) {
            state.accessToken = null
            state.refreshToken = null
            localStorage.removeItem('UserToken')
        },
        updateaccessdns(state, {
            type,
            dnsip
        }) {
            state.accesstype = type
            state.dns = dnsip
        },
    },
    getters: {
        loggedIn(state) {
            state.accessToken = localStorage.getItem('UserToken')
            return state.accessToken != null
        },
        isAuthenticated(state) {
            return state.accessToken
        },
        getaccesstypedns(state) {
            return { accesstype: state.accesstype, dns: state.dns }
        },
    },
    actions: {
    commitparams(context, params) {
        context.commit('updateaccessdns', {
            type: params.accesstype,
            dnsip: params.dns
        })
    },


    userLogout(context) {
        if (context.getters.loggedIn) {
            context.commit('destroyToken')
        }
    },
    userLogin(context, usercredentials) {
        return new Promise((resolve, reject) => {
            getAPI.post('users/token/', {
                username: usercredentials.username,
                password: usercredentials.password
            })
                .then(response => {
                    context.commit('updateStorage', { access: response.data.access, refresh: response.data.refresh })
                    resolve()
                })
                .catch(err => {
                    reject(err)
                })
        })
    }
}
})