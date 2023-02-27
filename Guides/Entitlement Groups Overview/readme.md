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
The built-in Data groups doesn't give any explicit permissions, but is the base groups used on the Access Control List (ACL) for data ingested into OSDU. It is recommended to create your own data groups with explicit access according to your requirements in terms of access control, as all users will be granted access to the data.default.owners by default, which is generally not desired.

Group Name                   | Description
-----------------------------|------------------
data.default.owners          | Gives read/write permissions to data stored with default ACL list
data.default.viewers         | Gives read only permissions to data stored with default ACL list

### Service Groups
The Service groups gives access to use the core services (APIs) and Dynamic Data Management Services (DDMS).

Group Name                    | Services         | API                      | Permissions 
------------------------------|------------------|--------------------------|-----------------------------
service.entitlements.admin    | Entitlements     | /entitlements/v2/groups<br>/entitlements/v2/members | GET, POST, PATCH, DELETE
service.entitlements.user     | Entitlements     | /entitlements/v2/groups<br>/entitlements/v2/members | GET
service.file.editors          | File             | |
service.file.viewers          | File             | |
service.legal.admin           | Legal            | |
service.legal.editor          | Legal            | |
service.legal.user            | Legal            | |
service.messaging.user        | Notification     | |
service.plugin.user           | | | 
service.search.admin          | Search           | |
service.search.user           | Search           | |
service.schema-service.admin  | Schema           | | 
service.schema-service.editors| Schema           | | 
service.schema-service.viewers| Schema           | |
service.storage.admin         | Storage          | |
service.storage.creator       | Storage          | |
service.storage.viewer        | Storage          | |
service.workflow.admin        | Workflow         | | 
service.workflow.creator      | Workflow         | | 
service.workflow.viewer       | Workflow         | | 

### User Groups
User groups are used to gather a number of users and grant access across multiple ***Service Groups*** and ***Data Groups***. They can also be nested within other ***User Groups***. 

Group Name             | Description
-----------------------|-------------
users                  | This group contains all users of the partition. The user principal or identity **needs** to belong to this group for you to be able to access the partition.
users.data.root        | This group provides permission to all data entities on the partition. It is getting associated to all the custom data entity groups and custom user groups as part of their creation.
users.datalake.viewers | This user group is meant for viewer level authorization.
users.datalake.editors | This user group is meant for editor level authorization and to authorize the creation of data with the Storage API.
users.datalake.admins  | This user group is meant for admin level authorization.
users.datalake.ops     | This user group is meant for operations level authorization. Association with this group provides the highest level of access to all the services and data in a partition.

#### User Groups Membership Matrix
Explains all the default groups that the different Users Groups are members of.

Group Name                     | users | users.datalake.viewers | users.datalake.editors | users.datalake.admins | users.datalake.ops
 ------------------------------|:-----:|:----------------------:|:----------------------:|:---------------------:|:------------------:
data.default.owners            |   X   |                        |                        |                       | 
data.default.viewers           |   X   |                        |                        |                       | 
service.entitlements.admin     |       |                        |                        |         **X**         |          X
service.entitlements.user      |       |          X             |           X            |           X           |          X
service.file.editors           |       |                        |         **X**          |           X           |          X
service.file.viewers           |       |          X             |           X            |           X           |          X
service.legal.admin            |       |                        |                        |                       |        **X**
service.legal.editor           |       |                        |         **X**          |           X           |          X
service.legal.user             |       |          X             |           X            |           X           |          X
service.messaging.user         |       |          X             |           X            |           X           |          X
service.plugin.user            |       |          X             |           X            |           X           |          X
service.schema-service.admin   |       |                        |                        |                       |        **X**
service.schema-service.editors |       |                        |         **X**          |           X           |          X
service.schema-service.viewers |       |          X             |           X            |           X           |          X
service.search.admin           |       |                        |                        |         **X**         |          X
service.search.user            |       |          X             |           X            |           X           |          X
service.storage.admin          |       |                        |                        |                       |        **X**
service.storage.creator        |       |                        |         **X**          |           X           |          X
service.storage.viewer         |       |          X             |           X            |           X           |          X
service.workflow.admin         |       |                        |                        |         **X**         |          X
service.workflow.creator       |       |                        |         **X**          |           X           |          X
service.workflow.viewer        |       |          X             |           X            |           X           |          X