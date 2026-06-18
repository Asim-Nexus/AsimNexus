# AsimNexus Nepal Ecosystem — Permission System

## Role-Based Permissions

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                    PERMISSION SYSTEM — ROLE-BASED ACCESS CONTROL                                   │
│                    "कसको केही गर्न अनुमति छ, कसको छैन?"                                             │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## User Roles & Permissions

| Role | Can Create | Can Update | Can Delete | Can View |
|------|------------|------------|------------|----------|
| **Citizen** | personal_ecosystem | personal_ecosystem | personal_ecosystem | personal + public |
| **Company** | company_ecosystem | company_ecosystem | company_ecosystem | company + public |
| **Government** | government_ecosystem | government_ecosystem | government_ecosystem | all |
| **Admin (System)** | all | all | all | all (Audit Only) |
| **Hybrid** | hybrid_ecosystem | hybrid_ecosystem | hybrid_ecosystem | hybrid |

## Permission Check Code

```python
# security/permission_check.py

class PermissionChecker:
    def __init__(self):
        self.permissions = {
            "citizen": {
                "can_create": ["personal_ecosystem"],
                "can_update": ["personal_ecosystem"],
                "can_delete": ["personal_ecosystem"],
                "can_view": ["personal_ecosystem", "public_ecosystem"]
            },
            "company": {
                "can_create": ["company_ecosystem"],
                "can_update": ["company_ecosystem"],
                "can_delete": ["company_ecosystem"],
                "can_view": ["company_ecosystem", "public_ecosystem"]
            },
            "government": {
                "can_create": ["government_ecosystem"],
                "can_update": ["government_ecosystem"],
                "can_delete": ["government_ecosystem"],
                "can_view": ["all_ecosystem"]
            },
            "admin": {
                "can_create": ["all_ecosystem"],
                "can_update": ["all_ecosystem"],
                "can_delete": ["all_ecosystem"],
                "can_view": ["all_ecosystem"]
            }
        }
    
    async def check_permission(self, user_role: str, action: str, ecosystem_type: str) -> bool:
        role_permissions = self.permissions.get(user_role)
        if not role_permissions:
            return False
        
        allowed_actions = role_permissions.get(action, [])
        if ecosystem_type in allowed_actions:
            return True
        
        if user_role == "admin":
            return True
        
        return False
```

## Cross-Ecosystem Permission

```python
# security/cross_ecosystem_permission.py

class CrossEcosystemPermission:
    async def request_access(self, user_id: str, ecosystem_id: str, action: str):
        """अरूको Ecosystem मा Access Request"""
        owner = await self._get_ecosystem_owner(ecosystem_id)
        request_id = await self._send_request(owner, user_id, action)
        response = await self._wait_for_response(request_id)
        
        if response == "approved":
            await self._grant_access(user_id, ecosystem_id, action)
            return {"status": "approved"}
        else:
            return {"status": "rejected"}
```

## Permission Flow

```
User Request → Permission Check → 51/49 Check → Consent → ZKP Filter → Action → Audit
```

## Consent Requirements

| Action Type | Consent Required |
|-------------|------------------|
| Self Ecosystem | ❌ No (Permission Check Only) |
| Cross-Ecosystem | ✅ Yes (Owner Consent) |
| Government → Company | ✅ Yes (Policy Consent) |
| Company → Government | ✅ Yes (Legal Consent) |
| Citizen → Anyone | ✅ Yes (Explicit Consent) |

## Audit Trail

All permission decisions are logged:
- User ID
- Action Taken
- Ecosystem Type
- Decision (Allowed/Blocked)
- Timestamp
- Reason