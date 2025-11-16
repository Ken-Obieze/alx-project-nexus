# **Online Polling System – Product Requirements Document (PRD)**

## **1\. Product Overview**
The Online Polling System is a secure and scalable platform designed to support organizational elections and online voting. It enables:
* Users to create accounts and participate in elections.
* Organization admins to create organizations, manage members, and run elections.
* Super admins to oversee the entire platform.
The system supports authentication, membership workflows, ballot creation, voting, result viewing, and role-based access.

---

## **2\. User Roles & Permissions**

### **2.1 Regular User**
* Create a platform account.
* Request membership in an organization.
* Vote in approved elections.
* View organization-specific elections and results (if allowed).

### **2.2 Organization Admin**
* Create and manage an organization.
* Approve or reject membership requests.
* Manage voters and sub-accounts.
* Create elections, positions, and candidates.
* Set election timelines and result visibility.
* View and export results.

### **2.3 Super Admin**
* Manage global platform users.
* Suspend or restore organizations.
* View all elections and data.
* Configure global system settings.
* Perform conflict resolution and admin overrides.

---

## **3\. Key Features**

### **3.1 User Management**
* Email/password authentication (JWT).
* Profile management.
* Password reset (OTP/email).
* Role-based access control.

### **3.2 Organization Management**
* Create and update organization details.
* User membership requests and approval.
* Admin controls voter list and access.

### **3.3 Election Management**
* Create and configure elections.
* Add positions/posts.
* Add candidates.
* Set time windows for voting.
* Publish or restrict election results.

### **3.4 Voting System**
* Secure one-vote-per-position enforcement.
* Vote anonymity.
* Real-time or end-time results.
* Duplicate-vote prevention.

### **3.5 Membership Workflow**
* Users request to join organizations.
* Organization admins approve or deny.
* Approved members become eligible voters.

### **3.6 Notifications (Optional)**
* Membership decisions.
* Election reminders.
* Result announcements.

### **3.7 Audit Logging**
* Logs admin actions.
* Authentication events.
* Election-related actions.
* Vote events (anonymized).

---

## **4\. System Requirements**

### **4.1 Functional Requirements**

#### **Authentication**
* Signup, login, logout.
* Token refresh.
* Password reset with OTP.

#### **Organization**
* Create and manage organizations.
* Search and join requests for users.
* Admin approval system.

#### **Election**
* Create elections with start/end times.
* Configure visibility of results.
* Immutable data after election start.

#### **Positions**
* Create and arrange positions for elections.

#### **Candidates**
* Add members as candidates.
* Option for external candidate entries.

#### **Voting**
* One vote per position per user.
* Anonymous vote records.
* Prevent multiple submissions.

#### **Results**
* Automatic tallying.
* Visible based on election settings.

---

### **4.2 Non-Functional Requirements**

#### **Security**
* Secure password hashing.
* Rate limiting.
* Encrypted sensitive data.
* Prevention of multiple votes.

#### **Performance**
* Scale up to 50k–100k voters per organization.
* Efficient real-time counting.

#### **Reliability**
* Transaction guarantees for votes.
* Retry queue for notifications.

#### **Compliance**
* Data protection principles.
* Guaranteed voter anonymity.

---

## **5\. Database Requirements (High-Level)**

### **Users**
| Field | Description |
| ----- | ----- |
| id | unique identifier |
| email | user email |
| password | hashed password |
| firstName | first name |
| lastName | last name |
| role | super\_admin, org\_admin, user |
| status | active, suspended |
| timestamps | createdAt, updatedAt |

### **Organizations**
| Field | Description |
| ----- | ----- |
| id | unique identifier |
| name | organization name |
| slug | url-friendly identifier |
| description | summary |
| ownerId | creator/admin |
| status | active or suspended |
| timestamps | createdAt, updatedAt |

### **OrganizationMembers**
| Field | Description |
| ----- | ----- |
| id | unique identifier |
| userId | linked user |
| organizationId | linked organization |
| role | admin, voter |
| membershipStatus | pending, approved, rejected |
| timestamps | createdAt, updatedAt |

### **Elections**
| Field | Description |
| ----- | ----- |
| id | unique identifier |
| organizationId | associated organization |
| title | election name |
| description | details |
| startAt | start time |
| endAt | end time |
| status | scheduled, ongoing, completed |
| resultVisibility | public or private |
| timestamps | createdAt, updatedAt |

### **Positions**
| Field | Description |
| ----- | ----- |
| id | unique identifier |
| electionId | linked election |
| title | position name |
| description | optional |
| orderIndex | ordering |
| timestamps | createdAt, updatedAt |

### **Candidates**
| Field | Description |
| ----- | ----- |
| id | unique identifier |
| positionId | linked position |
| userId | optional linked user |
| name | candidate name |
| manifesto | optional text |
| photoUrl | optional image |
| timestamps | createdAt, updatedAt |

### **Votes**
| Field | Description |
| ----- | ----- |
| id | unique identifier |
| voterId | organization member ID |
| candidateId | chosen candidate |
| positionId | linked position |
| electionId | linked election |
| createdAt | timestamp |

### **AuditLogs**
| Field | Description |
| ----- | ----- |
| id | unique identifier |
| userId | who performed action |
| actionType | e.g., create, update |
| entityType | user, election, etc. |
| entityId | ID of entity affected |
| metadata | extra info (JSON) |
| createdAt | timestamp |

---

## **6\. Core Workflows**

### **6.1 Signup Workflow**
1. User registers.
2. Optional email verification.
3. Role defaults to user.

### **6.2 Organization Creation**
1. User creates organization.
2. User becomes org admin.
3. Organization becomes active.

### **6.3 Membership Request**
1. User requests to join org.
2. Admin reviews request.
3. Approve → user becomes voter.

### **6.4 Election Creation**
1. Admin creates election.
2. Adds positions and candidates.
3. Sets timeline.
4. Publishes election.

### **6.5 Voting**
1. Election enters “ongoing” state.
2. Voter chooses candidates.
3. System validates voter eligibility.
4. Vote stored anonymously.
5. User cannot vote again.

### **6.6 Result Visibility**
* After end time, results are automatically available based on visibility settings.

---

## **7\. High-Level API Endpoints**

### **Authentication**
* `POST /auth/signup`
* `POST /auth/login`
* `POST /auth/forgot-password`
* `POST /auth/reset-password`

### **Organizations**
* `POST /organizations`
* `GET /organizations`
* `PATCH /organizations/:id`
* `DELETE /organizations/:id`

### **Membership**
* `POST /organizations/:id/join`
* `GET /organizations/:id/members`
* `PATCH /organizations/:id/members/:memberId`

### **Elections**
* `POST /organizations/:id/elections`
* `GET /organizations/:id/elections`
* `GET /elections/:id`
* `PATCH /elections/:id`

### **Positions**
* `POST /elections/:id/positions`
* `PATCH /positions/:id`

### **Candidates**
* `POST /positions/:id/candidates`
* `PATCH /candidates/:id`

### **Voting**
* `POST /elections/:id/vote`
* `GET /elections/:id/results`

---

## **8\. Milestones**

### **MVP**
* Authentication
* Organizations & membership
* Elections \+ positions \+ candidates
* Voting system
* Result display
* Basic admin management

### **V2**
* Multi-admin per organization
* Audit logs
* System analytics
* Notification system

---