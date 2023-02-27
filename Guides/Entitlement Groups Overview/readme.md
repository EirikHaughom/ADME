## Overview
This is intended as a best-effort to list the available default OSDU Entitlements Groups and their usage.

## Group Roles
There are two main group roles for which users and app registrations can be assigned.
| Role Name | Description                                        |
|-----------|----------------------------------------------------|
| MEMBER    | Regular member of the group                        |
| OWNER     | Provides permission to manage members of the group |

## Default Groups
The following groups are default in any OSDU, and thus also Microsoft Energy Data Services, instances.

### Data Groups
The built-in Data groups doesn't give any explicit permissions, but is the base groups used on the Access Control List (ACL) for data ingested into OSDU. It is more common to create your own data groups with explicit access according to your requirements in terms of access control.

Group Name                   | Description
-----------------------------|------------------
data.default.owners          | Gives read/write permissions to data stored with default ACL list
data.default.viewers         | Gives read only permissions to data stored with default ACL list

### Service Groups
The Service groups gives access to use the core services (APIs) and Dynamic Data Management Services (DDMS).

Group Name                   | Services | API              | Permissions |
|------------------------------|------------------|-------------------|-----------------------------|
|service.entitlements.admin    | Entitlements | /entitlements/v2/groups | GET, POST, PATCH, DELETE |
|service.entitlements.user     | Entitlements | /entitlements/v2/groups | GET, PATCH |
|service.legal.admin           ||||
|service.legal.editor          ||||
|service.legal.user            ||||
|service.storage.admin         ||||
|service.storage.creator       ||||
|service.storage.viewer        ||||
|service.schema-service.admin  ||||
|service.schema-service.editors||||
|service.schema-service.viewers||||
|service.file.editors          ||||
|service.file.viewers          ||||
|service.messaging.user        ||||
|service.search.admin          ||||
|service.search.user           ||||
|service.workflow.admin        ||||
|service.workflow.creator      ||||
|service.workflow.viewer       ||||
|service.plugin.user           ||||

### User Groups
User groups are used to gather a number of users and grant access across multiple ***Service Groups*** and ***Data Groups***. They can also be nested within other ***User Groups***. 

Group Name             | Description
-----------------------|-------------
users                  | Base authentication group. All users will need to be member of this group to be able to authorize to the other OSDU services.
users.datalake.viewers | 
users.datalake.editors | 
users.datalake.admins  | 
users.datalake.ops     | 

#### User Groups Membership Matrix
Explains all the default groups that the different Users Groups are members of.

Group Name                     | users | users.datalake.viewers | users.datalake.editors | users.datalake.admins | users.datalake.ops
 ------------------------------|-------|------------------------|------------------------|-----------------------|-----------
data.default.owners            |   X   |                        |                        |                       | 
data.default.viewers           |   X   |                        |                        |                       | 
service.entitlements.admin     |       |                        |                        |                       | 
service.entitlements.user      |       |          X             |           X            |                       | 
service.legal.admin            |       |                        |                        |                       | 
service.legal.editor           |       |                        |           X            |                       | 
service.legal.user             |       |          X             |           X            |                       | 
service.storage.admin          |       |                        |                        |                       | 
service.storage.creator        |       |                        |           X            |                       | 
service.storage.viewer         |       |          X             |           X            |                       | 
service.schema-service.admin   |       |                        |                        |                       | 
service.schema-service.editors |       |                        |                        |                       | 
service.schema-service.viewers |       |          X             |                        |                       | 
service.file.editors           |       |                        |                        |                       | 
service.file.viewers           |       |          X             |                        |                       | 
service.messaging.user         |       |          X             |                        |                       | 
service.search.admin           |       |                        |                        |                       | 
service.search.user            |       |          X             |                        |                       | 
service.workflow.admin         |       |                        |                        |                       | 
service.workflow.creator       |       |                        |                        |                       | 
service.workflow.viewer        |       |          X             |                        |                       | 
service.plugin.user            |       |          X             |                        |                       | 