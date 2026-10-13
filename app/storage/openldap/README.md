# OpenLDAP

OpenLDAP ([jp-gouin/helm-openldap](https://github.com/jp-gouin/helm-openldap)) is
the user and group directory for ownCloud Infinite Scale. With
`externalUserManagement` the oCIS chart drops its bundled IDM and expects an
external LDAP, as in the chart's
[external-user-management example](https://github.com/BadaBoum13/ocis-charts/blob/main/deployments/external-user-management/helmfile.yaml).
Auth0 handles login; oCIS creates the LDAP user on first login (autoprovisioning).

It runs in the `owncloud` namespace so it and oCIS can read the same OpenBao
entries. vault-config-operator generates them once (`crd/random-secrets.yaml`,
password policy `vco-openldap`), key `password`, never rotated:

| OpenBao path | Used for |
|---|---|
| `secret/owncloud/openldap-admin` | `cn=admin,dc=owncloud,dc=com`, also the oCIS bind password |
| `secret/owncloud/openldap-config` | `cn=admin,cn=config` |

## Resources

- [OpenLDAP Documentation](https://www.openldap.org/doc/)
- [Helm Chart values reference](https://github.com/jp-gouin/helm-openldap/blob/master/values.yaml)
