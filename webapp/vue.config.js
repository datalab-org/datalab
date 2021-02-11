module.exports = {
  configureWebpack: config => {
    config.externals = {
	...config.externals,
	"bokeh":"Bokeh",
    }
  },
}

