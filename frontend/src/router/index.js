import Vue from 'vue'
import VueRouter from 'vue-router'
import Dashboard from '../components/Dashboard.vue'
import Configuration from '../components/Configuration.vue'
import Inventory from '../components/Inventory.vue'
import TroubleShoot from '../components/TroubleShoot.vue'
import Login from '../components/Login.vue'
import SingleDevice from '../components/SingleDevice.vue'
import Topology from '../components/Topology.vue'
import PageNotFound from '../components/PageNotFound.vue'


Vue.use(VueRouter)

const routes = [{
        path: '/',
        name: 'dashboard',
        component: Dashboard,
        meta: {
            requiresLogin: true
        }
    },
    {
        path: '/configuration',
        name: 'configuration',
        component: Configuration,
        meta: {
            requiresLogin: true
        }
    },
    {
        path: '/inventory',
        name: 'inventory',
        component: Inventory,
        meta: {
            requiresLogin: true
        }
    },
    {
        path: '/host/:name',
        name: 'SingleDevice',
        props: true,
        component: SingleDevice,
        meta: {
            requiresLogin: true
        }
    },
    {
        path: '/topology',
        name: 'topology',
        component: Topology,
        meta: {
            requiresLogin: true
        }
    },
    {
        path: '/troubleshoot',
        name: 'troubleshoot',
        component: TroubleShoot,
        meta: {
            requiresLogin: true
        }
    },
    {
        path: '/login',
        name: 'login',
        component: Login,
        meta: {
            hidenavbar: true
        }
    },

    {
        path: "*",
        component: PageNotFound,
        meta: {
            hidenavbar: true
        }
    }
]

const router = new VueRouter({
    routes,
    mode: "history"
})

export default router