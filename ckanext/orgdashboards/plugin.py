import logging

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.lib.plugins as lib_plugins
import ckanext.orgdashboards.helpers as helpers

from routes.mapper import SubMapper
from pylons import config

log = logging.getLogger(__name__)

class OrgDashboardsPlugin(plugins.SingletonPlugin, lib_plugins.DefaultOrganizationForm):
    
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IGroupForm, inherit=True)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IFacets, inherit=True)

    ## IRoutes

    def before_map(self, map):
        # Define dashboard controller routes
        
        ctrl = 'ckanext.orgdashboards.controllers.dashboard:DashboardsController'
        map.connect('/organization/{name}/dashboard', controller=ctrl, 
                    action='organization_dashboard')
            
        return map

    ## IGroupForm

    def is_fallback(self):
        return False
    
    def group_types(self):
        return ['organization']

    def form_to_db_schema_options(self, options):
        ''' This allows us to select different schemas for different
        purpose eg via the web interface or via the api or creation vs
        updating. It is optional and if not available form_to_db_schema
        should be used.
        If a context is provided, and it contains a schema, it will be
        returned.
        '''
        schema = options.get('context', {}).get('schema', None)
        if schema:
            return schema

        if options.get('api'):
            if options.get('type') == 'create':
                return self.form_to_db_schema_api_create()
            else:
                return self.form_to_db_schema_api_update()
        else:
            return self.form_to_db_schema()

    def form_to_db_schema_api_create(self):
        schema = super(OrgDashboardsPlugin, self).form_to_db_schema_api_create()
        schema = self._modify_group_schema(schema)
        return schema

    def form_to_db_schema_api_update(self):
        schema = super(OrgDashboardsPlugin, self).form_to_db_schema_api_update()
        schema = self._modify_group_schema(schema)
        return schema

    def form_to_db_schema(self):
        schema = super(OrgDashboardsPlugin, self).form_to_db_schema()
        schema = self._modify_group_schema(schema)
        return schema

    def _modify_group_schema(self, schema):

        # Import core converters and validators
        _convert_to_extras = toolkit.get_converter('convert_to_extras')
        _ignore_missing = toolkit.get_validator('ignore_missing')

        default_validators = [_ignore_missing,_convert_to_extras]
        schema.update({
            'org_dashboard_header': default_validators,
            'org_dashboard_footer': default_validators,
            'org_dashboard_copyright': default_validators,
            'org_dashboard_lang_is_active': default_validators,
            'org_dashboard_base_color': default_validators,
            'org_dashboard_secondary_color': default_validators,
            'org_dashboard_is_active': default_validators,
            'org_dashboard_datasets_per_page': default_validators,
            'org_dashboard_charts': default_validators,
            'org_dashboard_map': default_validators,
            'org_dashboard_map_main_property': default_validators,
            'org_dashboard_main_color': default_validators,
            'org_dashboard_new_data_color': default_validators,
            'org_dashboard_all_data_color': default_validators,
        })
        
        charts = {}
        for _ in range(1, 7):
            charts.update({'org_dashboard_chart_{idx}'.format(idx=_): default_validators,
                           'org_dashboard_chart_{idx}_subheader'.format(idx=_): default_validators})
            
        schema.update(charts)
        return schema

    def db_to_form_schema(self):

        # Import core converters and validators
        _convert_from_extras = toolkit.get_converter('convert_from_extras')
        _ignore_missing = toolkit.get_validator('ignore_missing')
        _ignore = toolkit.get_validator('ignore')
        _not_empty = toolkit.get_validator('not_empty')

        schema = super(OrgDashboardsPlugin, self).form_to_db_schema()

        default_validators = [_convert_from_extras, _ignore_missing]
        schema.update({
            'org_dashboard_header': default_validators,
            'org_dashboard_footer': default_validators,
            'org_dashboard_copyright': default_validators,
            'org_dashboard_lang_is_active': default_validators,
            'org_dashboard_base_color': default_validators,
            'org_dashboard_secondary_color': default_validators,
            'org_dashboard_is_active': default_validators,
            'org_dashboard_datasets_per_page': default_validators,
            'org_dashboard_charts': default_validators,
            'org_dashboard_map': default_validators,
            'org_dashboard_map_main_property': default_validators,
            'org_dashboard_main_color': default_validators,
            'org_dashboard_new_data_color': default_validators,
            'org_dashboard_all_data_color': default_validators,
            'num_followers': [_not_empty],
            'package_count': [_not_empty],
        })
        
        charts = {}
        for _ in range(1, 7):
            charts.update({'org_dashboard_chart_{idx}'.format(idx=_): default_validators,
                           'org_dashboard_chart_{idx}_subheader'.format(idx=_): default_validators})
            
        schema.update(charts)
        return schema
    
    ## IActions

    def get_actions(self):

        module_root = 'ckanext.orgdashboards.logic.action'
        action_functions = _get_logic_functions(module_root)

        return action_functions

    def get_helpers(self):
        return {
            '_get_newly_released_data':
                helpers._get_newly_released_data,
            '_convert_time_format':
                helpers._convert_time_format,
            'montrose_replace_or_add_url_param':
                helpers._replace_or_add_url_param,
            'organization_list':
                helpers.organization_list,
            'get_org_chart_views':
                helpers.org_views.get_charts,
            '_get_chart_resources':
                helpers.get_resourceview_resource_package,
            'get_org_map_views': 
                helpers.org_views.get_maps,
            '_get_resource_url':
                helpers._get_resource_url,
            '_get_geojson_properties': 
                helpers._get_geojson_properties,
            '_get_resource_view_url':
                lambda id, dataset: '/dataset/{0}/resource/{1}'\
                                    .format(dataset, id)
        }
        
    ## IConfigurer
    
    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_resource('fanstatic', 'orgdashboards')
        toolkit.add_public_directory(config, 'public')
        
def _get_logic_functions(module_root, logic_functions = {}):
    module = __import__(module_root)
    for part in module_root.split('.')[1:]:
        module = getattr(module, part)

    for key, value in module.__dict__.items():
        if not key.startswith('_') and  (hasattr(value, '__call__')
                    and (value.__module__ == module_root)):
            logic_functions[key] = value
            
    return logic_functions
        