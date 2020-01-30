import graphviz
dot = graphviz.Digraph()
dot.attr('edge',arrowsize='0.5')
dot.render('test-output/rovppextrapolator2.gv')