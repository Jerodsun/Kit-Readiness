from dash import Input, Output

def register_callbacks(app):
    @app.callback(
        Output('dashboard-content', 'children'),
        [Input('tabs', 'active_tab')]
    )
    def update_dashboard(active_tab):
        if active_tab == 'tab-1':
            return 'Dashboard content for Tab 1'
        elif active_tab == 'tab-2':
            return 'Dashboard content for Tab 2'
        elif active_tab == 'tab-3':
            return 'Dashboard content for Tab 3'
        return 'Select a tab to see dashboard content'
