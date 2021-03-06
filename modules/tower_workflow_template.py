#!/usr/bin/python
# coding: utf-8 -*-
#
# (c) 2018, Adrien Fleury <fleu42@gmail.com>
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}


DOCUMENTATION = '''
---
module: tower_workflow_template
author: "Adrien Fleury (@fleu42)"
version_added: "2.6"
short_description: create, update, or destroy Ansible Tower workflow template.
description:
    - Create, update, or destroy Ansible Tower workflows. See
      U(https://www.ansible.com/tower) for an overview.
options:
    allow_simultaneous:
      description:
        - If enabled, simultaneous runs of this job template will be allowed.
      required: False
      type: bool
    description:
      description:
        - The description to use for the workflow.
      required: False
      default: null
    extra_vars:
      description:
        - >
          Extra variables used by Ansible in YAML or key=value format.
      required: False
    name:
      description:
        - The name to use for the workflow.
      required: True
    organization:
      description:
        - The organization the workflow is linked to.
      required: False
    schema:
      description:
        - >
          The schema is a JSON- or YAML-formatted string defining the
          hierarchy structure that connects the nodes. Refer to Tower
          documentation for more information.
      required: False
    survey_enabled:
      description:
        - Setting that variable will prompt the user for job type on the
          workflow launch.
      required: False
      type: bool
    survey:
      description:
        - The definition of the survey associated to the workflow.
      required: False
    state:
      description:
        - Desired state of the resource.
      required: False
      default: "present"
      choices: ["present", "absent"]
extends_documentation_fragment: tower
'''


EXAMPLES = '''
- tower_workflow_template:
    name: Workflow Template
    description: My very first Worflow Template
    organization: My optional Organization
    schema: "{{ lookup(file, my_workflow.json }}"

- tower_worflow_template:
    name: Workflow Template
    state: absent
'''


RETURN = ''' # '''


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ansible_tower import (
    tower_argument_spec,
    tower_auth_config,
    tower_check_mode,
    HAS_TOWER_CLI
)

try:
    import tower_cli
    import tower_cli.exceptions as exc
    from tower_cli.conf import settings
except ImportError:
    pass


def main():
    argument_spec = tower_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True),
        description=dict(required=False),
        extra_vars=dict(required=False),
        organization=dict(required=False),
        allow_simultaneous=dict(type='bool', required=False),
        schema=dict(required=False),
        survey=dict(required=False),
        survey_enabled=dict(type='bool', required=False),
        state=dict(choices=['present', 'absent'], default='present'),
    ))

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    if not HAS_TOWER_CLI:
        module.fail_json(msg='ansible-tower-cli required for this module')

    name = module.params.get('name')
    state = module.params.get('state')

    json_output = {'workflow_template': name, 'state': state}

    tower_auth = tower_auth_config(module)
    with settings.runtime_values(**tower_auth):
        tower_check_mode(module)
        wfjt_res = tower_cli.get_resource('workflow')
        try:
            params = {}
            params['name'] = name

            if module.params.get('description'):
                params['description'] = module.params.get('description')

            if module.params.get('organization'):
                organization_res = tower_cli.get_resource('organization')
                try:
                    organization = organization_res.get(
                        name=module.params.get('organization'))
                    params['organization'] = organization['id']
                except exc.NotFound as excinfo:
                    module.fail_json(
                        msg='Failed to update organization source,'
                        'organization not found: {0}'.format(excinfo),
                        changed=False
                    )

            if module.params.get('survey'):
                params['survey_spec'] = module.params.get('survey')

            for key in ('allow_simultaneous', 'extra_vars', 'survey_enabled',
                        'description'):
                if module.params.get(key):
                    params[key] = module.params.get(key)

            if state == 'present':
                params['create_on_missing'] = True
                result = wfjt_res.modify(**params)
                json_output['id'] = result['id']
            elif state == 'absent':
                params['fail_on_missing'] = False
                result = wfjt_res.delete(**params)

            if module.params.get('schema') and state == 'present':
                wfjt_res.schema(
                    result['id'],
                    module.params.get('schema')
                )

        except (exc.ConnectionError, exc.BadRequest) as excinfo:
            module.fail_json(msg='Failed to update workflow template: \
                    {0}'.format(excinfo), changed=False)

    json_output['changed'] = result['changed']
    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
