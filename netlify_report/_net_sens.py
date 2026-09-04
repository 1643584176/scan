# -*- coding: utf-8 -*-
"""Netlify:查看敏感字段值"""
import json

site = json.load(open(r'D:\scan\netlify_report\_js\net_site_full.json', encoding='utf-8'))
user = json.load(open(r'D:\scan\netlify_report\_js\net_user_full.json', encoding='utf-8'))
acc = json.load(open(r'D:\scan\netlify_report\_js\net_account_full.json', encoding='utf-8'))

print('=== site 敏感字段 ===')
for k in ['jwt_secret', 'identity_instance_id', 'id_domain', 'deploy_hook', 'session_id',
          'analytics_instance_id', 'has_database', 'parent_user_id', 'build_image',
          'build_settings', 'deploy_origin', 'feature_flags', 'processing_settings',
          'traffic_rules_config_per_scope', 'jwt_roles_path', 'capabilities', 'plugins']:
    print('  %-30s: %s' % (k, json.dumps(site.get(k))[:150]))

print()
print('=== user 敏感字段 ===')
for k in ['uid', 'tracking_id', 'command_bar_signed_user_id', 'sandbox', 'slug', 'account_id',
          'favorite_sites', 'graphql_enabled', 'managed_by_sso_or_directory_sync', 'saml_account_id']:
    print('  %-40s: %s' % (k, json.dumps(user.get(k))[:150]))

print()
print('=== account 敏感字段 ===')
for k in ['site_jwt_secret', 'owner_ids', 'security_contacts', 'site_memberships',
          'member_roles', 'site_access', 'site_sso_login', 'site_sso_login_context',
          'site_password_context', 'payment_provider_id', 'ai_gateway_available_on_plan',
          'per_user_agent_runner_credit_limit', 'deploy_diagnostics_setting',
          'billing_details', 'capabilities']:
    print('  %-35s: %s' % (k, json.dumps(acc.get(k))[:150]))
