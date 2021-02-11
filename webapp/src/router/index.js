import { createRouter, createWebHistory } from 'vue-router'
// import Home from '../views/Home.vue'
// import Test from '../views/Test.vue'
import Samples from '../views/Samples.vue'
import NotFound from '../views/NotFound.vue'
import EditPage from '../views/EditPage.vue'

const routes = [
	{
		path: '/about',
		name: 'About',
		// route level code-splitting
		// this generates a separate chunk (about.[hash].js) for this route
		// which is lazy-loaded when the route is visited.
		component: () => import(/* webpackChunkName: "about" */ '../views/About.vue')
	},
	{
		path: '/samples',
		name: 'samples',
		alias: '/',
		component: Samples
	},
	{
		path: '/edit/:id',
		name: 'edit',
		component: EditPage,
	},
	{ path: '/404', name: 'notfound', component: NotFound },
	{ path: '/:pathMatch(.*)*', component: NotFound },
]

const router = createRouter({
	history: createWebHistory(process.env.BASE_URL),
	routes
})

export default router
