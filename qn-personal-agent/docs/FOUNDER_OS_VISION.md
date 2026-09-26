# QN — Founder-Level Autonomous Agent: Vision Spec

This is the full target architecture for QN, as defined by the founder — preserved verbatim below.
It is the north star, not the next pull request. See docs/ARCHITECTURE.md for the phased build order
that actually gets there without producing fake/stubbed components. Nothing here gets implemented
"all at once" — every piece must be independently verified (per docs/RULES.md's status vocabulary)
before the next is started. See docs/PERSONA.md for how QN communicates with the founder day to day.

---

# FOUNDER-LEVEL AUTONOMOUS AI AGENT

## Voice + Text + Browser + Local PC + Research + Coding + Automation + Persistent Memory + 24/7 Runtime + Multi-Agent Execution

Build a production-oriented, modular, continuously operating AI agent platform that functions as the founder's personal digital operating system and autonomous work environment.

This must NOT be built as a simple chatbot, static assistant, demo interface, simulated agent, collection of disconnected pages, or collection of buttons that pretend to perform actions.

Build a real working agent runtime in which the AI can understand what the founder wants, understand the context and objective, research how the objective can actually be accomplished, inspect the existing system, identify what capabilities already exist, identify what capabilities are missing, find appropriate tools, open-source projects, APIs, models, documentation and software, determine how those resources can be integrated, request the required permissions, execute the work, observe the execution, test the result, independently verify the result, save the resulting state, update the system registry, remember what happened, continue unfinished work, recover from failures, and report the actual verified state to the founder.

The system must operate primarily through a browser-based environment and remain capable of running continuously as a backend/background service. When a task can be completed using browser/remote capabilities, the agent should use browser/remote execution. When a task genuinely requires local computer resources, local software, local files, local GPU, Windows applications, terminal access, PowerShell, or another local capability, the agent must request the required local permission and activate the local bridge only for the authorized operation.

The browser interface is the founder's control center. It must not be the process that keeps the agent alive. The underlying runtime, workers, queues, scheduler, database, agents and services must continue operating independently of whether the browser tab is currently open.

The entire system must be modular so that additional agents, tools, skills, models, APIs, repositories, applications, automation providers, execution environments and capabilities can be added without rewriting the entire platform.

The central operating principle is:

UNDERSTAND → INSPECT CURRENT STATE → RESEARCH → PLAN → CHECK CAPABILITIES → REQUEST PERMISSION WHEN REQUIRED → EXECUTE → OBSERVE → TEST → VERIFY → REGISTER → SAVE STATE → CONTINUE → REPORT

Never use:

ASSUME → CLAIM SUCCESS → STOP

The AI model must never be the sole source of truth regarding whether an action actually happened. The runtime, tools, filesystem, database, browser state, process state, test results and verification layer must establish actual reality.

For every important operation, maintain an observable and persistent state.

For example, if the founder asks the agent to install an open-source repository, the agent must not simply say "repository installed." It must be able to establish:

repository discovered,
repository inspected,
repository selected,
repository source verified,
repository downloaded or cloned,
repository location verified,
license inspected,
dependencies detected,
environment requirements detected,
hardware requirements checked,
compatibility checked,
dependencies installed,
configuration completed,
installation test executed,
health check executed,
integration test executed,
tool registered,
capability registered,
version recorded,
location recorded,
dependencies recorded,
status changed to ACTIVE only after successful verification.

If something fails, the system must record the failure and continue with recovery, alternative research, retry, rollback, or founder approval as appropriate.

The founder must be able to communicate naturally through voice or text without needing to know the technical architecture.

The interface must support text input, microphone input, continuous voice conversation, voice interruption, speech-to-text, text-to-speech, file uploads, image uploads, video uploads, audio uploads, document uploads, URLs, repository URLs, API documentation URLs, YouTube URLs, YouTube Shorts URLs, Instagram URLs, TikTok URLs, Facebook URLs, X URLs, podcast URLs, music URLs, GitHub URLs, GitLab URLs, Hugging Face URLs, software URLs, documentation URLs, datasets, research papers, PDFs, business websites, SaaS platforms, cloud-storage references and other web resources.

When the founder says something such as "Build me a video editing agent," the system must automatically understand the requested outcome and internally determine what is being requested, what the inputs are, what capabilities are required, what tools are required, what agents are required, what open-source projects are available, what commercial or free services may be available, what documentation exists, what APIs exist, what dependencies are required, what hardware is required, what already exists in the current system, what is missing, what can be reused, what must be installed, what must be coded, what must be configured, what must be tested, what requires permission, what can execute automatically, what is blocked, what remains unfinished and what must be verified before reporting completion.

The system must contain a natural-language requirement engine that converts founder requests into structured objectives, constraints, inputs, desired outputs, required capabilities, dependencies, permissions, execution environments, risks, verification requirements and completion conditions.

For example, if the founder says that they want an agent that can take a trending video, understand the video, replace the character with a provided character, preserve the movement and visual structure, create the resulting video and allow the founder to approve it, the agent should internally derive requirements such as video ingestion, video analysis, scene understanding, character detection, identity handling, pose/motion analysis, image/video generation, compositing, rendering, audio preservation or processing, preview generation, approval workflow, export and storage, while researching appropriate tools and determining whether each component should execute remotely or locally.

The system must include an Intent Engine capable of identifying one or multiple intents in the same request. Intents may include information retrieval, research, coding, debugging, software installation, repository analysis, browser automation, file operation, media processing, business operation, content creation, data analysis, communication, scheduling, monitoring, system administration, project creation, project modification, tool discovery, API integration, open-source integration, automation creation, multi-agent execution, long-running execution, deployment, testing, verification, maintenance, monitoring and recovery.

A single founder request may contain many intents and must be converted into an appropriate task graph rather than being treated as a single simplistic prompt.

The system must contain a URL Understanding Engine. Whenever the founder supplies a URL, the agent must first determine what kind of URL it is and why it was supplied before deciding what to do with it.

The system must recognize and appropriately process URLs representing websites, documentation, GitHub repositories, GitLab repositories, Hugging Face resources, API documentation, software downloads, npm packages, PyPI packages, Docker resources, YouTube videos, YouTube Shorts, Instagram content, TikTok content, Facebook content, X content, podcasts, music, audio, video, images, cloud storage, SaaS platforms, datasets, research papers, PDFs, business websites and other resources.

The agent must determine whether the URL is a reference, tool, project, source of information, software resource, documentation source, media reference, dataset, API, product, service or existing project.

The agent must not treat every URL as ordinary text.

When the founder provides a video reference, the system should analyze whatever information is legitimately accessible and relevant to the task, including subject, format, duration, visual structure, editing structure, transitions, effects, captions, pacing, camera movement, characters, objects, backgrounds, audio characteristics, scene structure and production techniques where technically and legally accessible.

When the founder provides music, podcast or other media references, the system should understand the relevant structure, topic, format, metadata, content characteristics and intended use, while respecting applicable access, copyright, platform and permission limitations.

When the founder provides a GitHub or other repository URL, the agent must inspect repository purpose, language, framework, license, dependency files, installation requirements, supported operating systems, hardware requirements, APIs, models, build process, examples, tests, releases, known limitations, current version, maintenance state and integration possibilities before deciding how to use it.

Create a dedicated Research Agent that can perform task-specific research across web resources, official documentation, GitHub, GitLab, open-source repositories, package registries, model repositories, API documentation, technical articles, research papers, software manuals and other legitimate sources.

Research must be driven by the actual task.

The agent must not perform random research merely to appear intelligent.

For each research operation, maintain the research question, search strategy, sources, findings, compatibility information, limitations, risks, uncertainties and implementation implications.

The system must distinguish verified facts, official documentation, observations, model-generated inference, assumptions and uncertainty. The agent must not present an inference as a verified fact.

When an open-source project is provided or required, the Open-Source Discovery Engine must inspect the repository, README, documentation, license, releases, dependency files, package configuration, installation instructions, examples, tests, supported platforms, hardware requirements, model requirements, API requirements and integration requirements.

Before installing an external repository, the agent must determine whether it can legally and technically be used for the intended purpose, whether its license is compatible with the intended use, whether it can run locally, whether it can run remotely, what resources it requires, what it provides, what it depends on, what security concerns exist, what code must be written around it and how it can be integrated into the existing architecture.

Never blindly install repositories.

Create a persistent Tool Registry.

Every software tool, open-source project, API integration, browser tool, model service, local application, containerized service, media processor, automation tool or other executable capability integrated into the system must have a persistent registry record containing a unique Tool ID, name, description, category, version, verified installation state, actual location, installation method, source repository, license information, dependencies, required hardware, configuration status, health status, last verification, supported capabilities, projects using the tool, execution environment, permissions, documentation reference and current status.

Tool status must distinguish at least:

DISCOVERED
DOWNLOADED
INSTALLED
CONFIGURED
TESTED
ACTIVE
FAILED
DISABLED
REMOVED
OUTDATED
BLOCKED
UNVERIFIED

Create a persistent Software Inventory that tracks installed software, versions, paths, dependencies, repositories, models, APIs, services, containers, browser extensions, local applications, remote services, credential references, configuration references, health status and relationships to projects and capabilities.

The agent must always be able to determine what already exists, what is missing, what is broken, what requires updating and what can be reused.

Create a persistent Capability Registry independent of the Software Registry.

The system must think in terms of capabilities rather than only individual software packages.

For example:

VIDEO_TRANSCRIPTION
VIDEO_RENDERING
IMAGE_GENERATION
VIDEO_GENERATION
WEB_RESEARCH
BROWSER_AUTOMATION
PDF_READING
CODE_EXECUTION
GITHUB_READ
GITHUB_WRITE
FILE_PROCESSING
VOICE_INPUT
VOICE_OUTPUT
DATABASE_ACCESS
LOCAL_PC_CONTROL
SCHEDULING
EMAIL_ACCESS
CONTENT_CREATION
DATA_ANALYSIS

Each capability must record its implementation, tools, versions, dependencies, execution environment, health state, permissions, projects using it and verification status.

When a task requires a capability, the agent must first query the Capability Registry.

If the capability exists and is healthy, reuse it.

If it exists but is unhealthy, diagnose and repair it.

If it exists but is incompatible, find an alternative.

If it does not exist, research how to acquire, build or integrate the capability.

This prevents unnecessary duplicate installations.

Create a persistent Project Registry.

Every project must have a Project ID, project name, description, owner, creation date, current version, repository, local path if applicable, remote location if applicable, status, architecture, dependencies, tools, agents, APIs, databases, execution environments, tasks, completed tasks, pending tasks, blocked tasks, known bugs, last test, last verification, last deployment, last modification, snapshots and recovery information.

The system must maintain project state automatically.

If a project contains completed, pending and blocked components, the system must know which components belong to which category based on actual stored state and verification rather than relying on the model's memory.

Create a Task Management Engine in which every complex request becomes a persistent Task Graph.

The graph must support parent tasks, child tasks, dependencies, parallel tasks, sequential tasks, conditional tasks, retryable tasks, blocked tasks, approval-required tasks, verification tasks, rollback tasks and long-running tasks.

Each task must contain an ID, parent, project, status, dependencies, inputs, outputs, required capabilities, required tools, permissions, start time, end time, result, error information, retry count, worker ID, execution ID, verification state and recovery state.

Task states must include:

QUEUED
PLANNING
RESEARCHING
WAITING_FOR_PERMISSION
READY
EXECUTING
WAITING_FOR_RESOURCE
VERIFYING
FAILED
RETRYING
BLOCKED
COMPLETED
CANCELLED
PAUSED

The UI must display these states in real time.

Create a powerful Permission Engine.

The agent must never receive unrestricted local authority simply because it is an AI agent.

Use capability-based permissions.

Permissions must cover reading web content, reading files, writing files, deleting files, running terminal commands, running PowerShell, installing software, modifying system configuration, using browser automation, downloading files, uploading files, accessing microphone, accessing camera, using APIs, sending messages, publishing content, accessing accounts, controlling desktop applications, creating repositories, modifying repositories, deploying services and other sensitive capabilities.

Each permission must support states such as:

ALLOWED
DENIED
ASK_EVERY_TIME
ASK_ONCE
PROJECT_ONLY
SESSION_ONLY

The founder must be able to configure permissions from the UI.

Sensitive operations must trigger a clear approval request.

For example, before installing a dependency, the agent must explain what it wants to install, why it is needed, where it will be installed, what permissions are required and what project will use it.

The founder should be able to choose:

ALLOW ONCE
ALLOW FOR PROJECT
ALLOW FOR SESSION
ALLOW ALWAYS
DENY

After approval, execute the operation, verify it and record the approval and result.

Never claim permission was granted when it was not.

Create a Browser Automation Agent as a complete execution tool rather than a placeholder.

The Browser Agent must support browser session management, multiple browser sessions where appropriate, tabs, navigation, back/forward operations, page loading, URL opening, DOM inspection, accessibility-tree inspection where available, structured page extraction, text extraction, element discovery, clicking, typing, keyboard interaction, scrolling, selecting, form completion, file downloads, file uploads, screenshots, page screenshots, viewport control, browser state management, cookies/session state where explicitly authorized, authentication flows where explicitly authorized, browser storage where permitted, JavaScript execution only where appropriate and permitted, page monitoring, content extraction, structured data extraction and verification of visible browser results.

The browser agent must understand websites as interactive applications rather than merely reading page text.

It must be able to navigate a multi-step website workflow, maintain the task context, recognize when a page has changed, identify whether an expected element exists, recover when the page structure changes, capture screenshots for verification, inspect errors, wait for dynamic content, handle appropriate loading states, detect authentication requirements and request founder interaction when credentials, MFA, CAPTCHA or other protected actions require human participation.

The browser agent must log every meaningful action.

For example:

browser session created,
URL opened,
page loaded,
element identified,
button clicked,
text entered,
file selected,
download initiated,
download completed,
result inspected,
screenshot captured,
operation verified.

Browser actions must have execution IDs and be associated with the current task.

The browser agent must never silently perform account-level actions that have not been authorized.

Create a Local PC Bridge as a separate controlled execution environment.

The Local Bridge must support, when explicitly authorized, Windows filesystem operations, terminal operations, PowerShell operations, installed applications, local Python environments, local Node environments, Git, local models, GPU resources, FFmpeg, desktop applications, local databases and other required local resources.

The browser agent must not directly obtain unrestricted operating-system control.

The architecture must be:

Browser/UI → Orchestrator → Permission Engine → Local Bridge → Local Tool → Verification → Result

The Local Bridge must remain inactive when local execution is unnecessary.

The system must determine whether a task can be completed in the browser/remote environment.

If yes, execute remotely/browser-side.

If no, determine exactly why local execution is required.

Examples include local GPU requirements, local files, local software, local databases, Windows applications, offline processing or hardware-dependent workloads.

When local execution is required, request the appropriate permission, activate the local bridge, perform only the required operation, verify the result, record the execution and return the result to the main runtime.

The local bridge should be able to shut down or return to an inactive state after the operation when appropriate.

Create a continuously running Agent Runtime.

The runtime must support persistent task queues, background workers, scheduled tasks, recurring tasks, event-driven tasks, monitoring, health checks, retries, crash recovery, task persistence, worker restart, heartbeat, logs, alerts, execution IDs and recovery from disconnected browser sessions.

The system must not depend on the founder keeping the browser tab open.

The browser is a control interface.

The backend runtime is the actual execution system.

Use an architecture conceptually equivalent to:

Founder UI ↔ API ↔ Orchestrator ↔ Persistent Queue ↔ Workers ↔ Agents ↔ Tools ↔ Verification ↔ Database

The browser UI must be able to disconnect and reconnect without losing the task.

Every long-running agent and worker must provide heartbeat information including online/offline state, current task, progress, current operation, worker ID, last heartbeat, health state and expected next operation.

Create an Agent Health Monitor that continuously monitors the API, database, workers, browser sessions, local bridge, queues, models, tools, storage, memory, CPU, GPU where available, network state, scheduler, task failures and other critical services.

Health states must include:

HEALTHY
DEGRADED
OFFLINE
FAILED
UNKNOWN

Create self-recovery mechanisms.

When an operation fails, the agent must capture the error, classify it, inspect relevant logs, determine whether retry is safe, retry when appropriate, modify the strategy when appropriate, research alternative solutions when required, request permission if the alternative requires additional privileges, retry using the new approach and report the exact blocker if recovery is unsuccessful.

The agent must not repeatedly execute a dangerous or destructive operation simply because a previous attempt failed.

Create a dedicated Coding Agent.

The Coding Agent must be able to inspect repositories, understand project architecture, inspect source files, locate relevant components, create files, modify files, refactor code, create APIs, build frontend components, build backend services, create database schemas, write tests, run tests, inspect errors, debug failures, read documentation, integrate external tools, install dependencies after permission, create branches, create commits, generate patches, prepare pull requests when authorized and explain what changed.

The Coding Agent must first inspect the existing project before modifying it.

It must determine the existing architecture, locate the relevant files, identify dependencies, identify existing functionality, determine what must actually change and avoid unnecessarily rewriting working components.

Before modifying a project, create an implementation plan, make the minimum necessary changes, execute tests, inspect failures, fix issues, verify functionality and record the changes.

Create a controlled Code Execution Sandbox.

Code execution must be isolated wherever possible using containers, restricted subprocesses, sandboxed environments, resource limits, filesystem boundaries and execution permissions.

The agent must know what code is being executed, where it is executing, which permissions it has, which files it can access, what network access it has, what resources it consumes and what output it generated.

Create a GitHub Agent.

The GitHub Agent must support repository search, repository inspection, README inspection, issue inspection, release inspection, dependency inspection, source download, cloning when permitted, branch inspection, commit inspection, branch creation, commit creation and pull-request creation when explicitly authorized.

Default GitHub access must be read-only.

Any write operation must require appropriate permission.

Create a complete memory architecture.

Do not place every type of memory into a single undifferentiated memory store.

Maintain short-term conversational context, current working-task memory, project memory, durable founder preferences where appropriate, technical knowledge memory, documentation memory, execution memory, audit memory and system-state memory.

Memory records must contain an ID, type, source, timestamp, project relationship, confidence, content, related task, expiration policy when applicable and access level.

The model must never silently invent memories.

The system must distinguish between actual stored state and model-generated assumptions.

Create a Knowledge Ingestion Engine.

When the founder supplies documentation, a repository, a PDF, a website, technical documentation, software manuals or other knowledge resources, the system must ingest the resource where permitted, parse it, index it, classify it, connect it to the relevant project or capability, preserve the source reference and record its version/date where available.

The agent must later be able to determine what was learned from that resource, what source supported the information, what changed between versions and whether the information remains relevant to the current implementation.

Live learning must NOT mean uncontrolled self-modification.

Live learning must operate as:

RESEARCH → EXTRACT → VALIDATE → STORE → APPLY

The agent may learn new procedures, tools, technical information and workflows, but critical system architecture, security policies, permission rules and production behavior must not silently change without controlled testing, verification and appropriate authorization.

Create specialized agents rather than forcing one model to perform every responsibility.

The minimum architecture should include an Orchestrator Agent, Research Agent, Browser Agent, Coding Agent, File Agent, System Agent, Media Agent, Data Agent, Testing Agent, Security Agent, Memory Agent, Monitoring Agent, Planning Agent and Verification Agent.

Additional specialized agents must be dynamically addable.

The Orchestrator must determine which agent or combination of agents should perform each task.

For example, if the founder asks to turn an existing GitHub project into a working website, the Orchestrator may assign repository inspection to the Research Agent, implementation to the Coding Agent, browser testing to the Browser Agent, test execution to the Testing Agent, independent validation to the Verification Agent and deployment to the deployment subsystem after authorization.

Create an independent Verification Agent.

The agent responsible for performing an operation must not automatically be trusted to declare that operation successful.

The Verification Agent must independently inspect the result.

For example, if the Coding Agent claims that login has been implemented, the Verification Agent should inspect the implementation, run relevant tests, test the login flow, inspect database state, inspect session behavior, inspect UI behavior and examine logs before marking the feature VERIFIED.

The system must have a truthful status system.

Every important component and task must distinguish:

PLANNED
STARTED
IN_PROGRESS
COMPLETED
VERIFIED
BLOCKED
FAILED
UNVERIFIED
PARTIAL
DISABLED
PRODUCTION_READY

Never display "DONE" or equivalent language when verification has not succeeded.

If implementation completed but verification is pending, display:

IMPLEMENTED — UNVERIFIED

If only part of a feature exists:

PARTIAL

If the feature does not exist:

NOT IMPLEMENTED

If testing succeeded:

VERIFIED

If all required production checks have passed:

PRODUCTION READY

Create a real-time activity system.

The founder must be able to watch the agent work in real time.

Display events such as:

Research Agent started.
Repository discovered.
Repository inspected.
Documentation loaded.
Dependency requirements identified.
Compatibility checked.
Permission required.
Permission granted.
Download started.
Download completed.
Installation started.
Installation completed.
Testing started.
Testing failed.
Error diagnosed.
Alternative researched.
Retry started.
Verification started.
Verification passed.
Capability registered.
Project state updated.

The activity log must show timestamps, task IDs, agent IDs and meaningful execution information.

Create a powerful founder dashboard.

The main interface must provide a persistent conversational area for voice and text, current task information, task plans, live activity, approval requests, projects, tools, capabilities, agent health, memory context where appropriate, files, browser sessions, local execution status, monitoring, logs, schedules, system health and diagnostics.

The interface must be highly usable and responsive rather than merely a collection of technical forms.

The founder should be able to see what the agent is currently doing, why it is doing it, what it is waiting for, what it needs from the founder, what has succeeded, what failed, what remains and what requires attention.

Provide a visual task graph showing the relationship between goal, requirements, research, dependencies, implementation, testing, verification, deployment and monitoring.

The graph must be generated dynamically from the actual Task Graph and database state rather than being a decorative static graphic.

Create automatic Tool Discovery.

When the founder requests a capability that does not currently exist, the agent must not simply answer "I can't do that."

It must determine the missing capability, search available tools and open-source projects, inspect APIs and documentation, evaluate compatibility, determine the safest implementation path, identify installation requirements, request permission where required, install or integrate the capability, test it, verify it and register it.

For example, if automatic subtitle generation is missing, the system should discover suitable transcription/subtitle technologies, determine compatibility, obtain approval if required, integrate the chosen capability, test it and register:

AUTO_SUBTITLES = ACTIVE

The system must automatically recognize newly available capabilities.

Create a Resource Manager that tracks CPU, RAM, GPU, VRAM, disk space, network availability, browser sessions, API limits, storage availability, model availability and other relevant resources.

Before starting expensive workloads, estimate resource requirements.

If the environment is insufficient, the agent must explain the limitation and research alternatives.

Create a Model Router.

Do not hard-code one model as the intelligence layer.

Support different model roles including fast reasoning, deep reasoning, coding, vision, audio, transcription, embeddings, image generation, video generation and other specialized workloads.

The model router should select models based on task requirements, quality, latency, cost, availability, privacy, hardware and provider constraints.

Support multi-model fallback.

If one model fails, the system may use an approved compatible alternative. Any model change must be recorded in execution state.

Never silently switch to an incompatible model.

Create secure API and secret management.

Never place API keys, passwords, access tokens or other sensitive credentials directly into source code.

Use secure secret handling.

The system may know that a credential exists without exposing its value.

Logs must automatically redact API keys, passwords, access tokens, cookies, session credentials and other sensitive values.

Create controlled account access.

External services must default to NO ACCESS.

The founder must explicitly authorize account access.

Separate READ, WRITE, PUBLISH and DELETE permissions.

Support services such as GitHub, YouTube, Instagram, Gmail, cloud storage, social media platforms and other external systems through permission-controlled connectors.

Create strict filesystem safety.

Maintain an agent workspace such as:

AGENT_WORKSPACE/
Projects/
Tools/
Models/
Downloads/
Temp/
Logs/
Memory/
Backups/
Repositories/
Artifacts/
Cache/

The agent should not automatically access arbitrary system directories.

Protected directories require explicit permission.

Create a backup and checkpoint system.

Before major modifications, create an appropriate snapshot, Git checkpoint, configuration backup or database backup.

Support rollback.

If a modification fails and rollback is safe, restore the previous verified state.

Create a complete audit log.

Record:

WHO
WHAT
WHEN
WHY
PROJECT
TASK
AGENT
TOOL
RESOURCE
PERMISSION
RESULT
VERIFICATION

The audit system must allow the founder to determine exactly what happened during an operation.

Create a 24/7 Scheduler.

Support one-time tasks, recurring tasks, interval tasks, cron-style schedules, event-triggered tasks, monitoring tasks, conditional tasks and long-running jobs.

For example, if the founder says:

"Every morning research new AI video tools."

The system should create a recurring task, execute it according to the schedule, record the research, compare new findings against the existing Tool and Capability Registries and notify the founder when relevant information or actionable changes are found.

Create an Event Engine.

Events may include new files, new emails where authorized, GitHub releases, website changes, scheduled times, task completion, task failure, service failure, new uploads, changes in registered tools, capability health changes and other configured events.

Events must be capable of triggering appropriate agents and workflows.

Create a Notification Engine supporting UI notifications, browser notifications, email where configured and authorized, voice notifications, task completion notifications, permission requests, failure alerts, system health alerts and security alerts.

Create a true voice agent.

Voice must not merely convert speech to text.

Use:

MICROPHONE → SPEECH-TO-TEXT → INTENT → CONTEXT → PLANNING → EXECUTION → RESULT → TEXT/VOICE RESPONSE

Support interruption.

If the founder says "Stop," cancellable operations should be paused or cancelled according to the task state and safety rules.

If the founder says "Continue," the agent should resume from the latest verified checkpoint when possible.

The voice system must support natural follow-up commands such as:

"Continue that."
"Use the same repository."
"Use the tool we installed earlier."
"Don't install anything yet."
"Open the project we were building."
"Run the test again."
"Why did that fail?"
"What is left?"
"Continue from where you stopped."

These references must be resolved using actual task, project and execution history.

If multiple possible references exist, ask for clarification rather than guessing.

The agent must maintain self-knowledge of its own actual system state.

It should be able to answer:

What agents exist?
What tools are installed?
What capabilities are active?
What projects are active?
What tasks are running?
What tasks failed?
What tasks are waiting for approval?
What permissions are enabled?
What capabilities are missing?
What software is installed?
What models are available?
What repositories are connected?
What was the last verified deployment?
What requires attention?
What is currently unhealthy?
What work remains?

Maintain a machine-readable System Map connecting agents, tools, models, projects, APIs, databases, browser systems, local bridge, permissions, schedulers, tasks, memory, workers and monitoring.

Every system component must have status and health information.

Implement a full system diagnosis command such as:

/diagnose

and equivalent voice command:

"Run a full system diagnosis."

The diagnostic system must inspect backend, frontend, database, queues, workers, browser, local bridge, tools, models, permissions, storage, memory, scheduler, network, logs, recent failures, active tasks, service health and critical dependencies.

The result must identify:

HEALTHY
DEGRADED
FAILED
OFFLINE
UNKNOWN
UNVERIFIED

Implement a full project/system audit command such as:

/audit

and equivalent natural-language request.

The audit must determine:

what has actually been built,
what is partially built,
what is missing,
what is broken,
what has not been tested,
what has been tested but not verified,
what is blocked,
what requires permission,
what dependencies are missing,
what tools are outdated,
what capabilities are unavailable,
what security issues exist,
what work remains and what is required for production readiness.

Create automatic project bootstrap.

When a new project is requested, create the project identity, workspace/repository, initial architecture, configuration, project registry record, task graph, dependency analysis and required capability analysis before implementation begins.

As work progresses, continuously update project state.

Maintain a dependency graph connecting:

PROJECTS → TOOLS → MODELS → APIS → SERVICES → DATABASES → CAPABILITIES

If a dependency becomes unavailable, determine which projects and capabilities are affected.

For example, if a video-rendering dependency becomes unavailable, identify every active capability and project depending upon it.

Track versions of tools, models, APIs, projects, schemas and other important dependencies.

Before updating a production dependency, check compatibility, current usage, release information, potential breaking changes and rollback options.

Create a comprehensive testing system supporting unit tests, integration tests, end-to-end tests, health tests, browser workflow tests, API tests, tool tests, capability tests and project-level verification.

The Browser Agent should be testable through real browser workflows such as opening a website, navigating, locating an element, interacting with it, extracting a result, capturing a screenshot and verifying the expected result.

The Media Agent should be testable by providing input media, processing it, rendering output and validating that the expected artifact exists and meets required properties.

Use event-driven real-time state synchronization.

The frontend should receive live task progress, agent status, permission requests, logs, errors, completion events and verification events through appropriate real-time mechanisms such as WebSocket or server-sent events.

Persist all important system state.

The database should maintain users, projects, tasks, task steps, agents, tools, capabilities, repositories, installations, models, permissions, credential metadata, events, logs, memories, documents, knowledge, executions, errors, health checks, schedules, snapshots, checkpoints, artifacts and relevant relationships.

Create strong observability through structured logs, metrics, traces, execution IDs, task IDs, project IDs, agent IDs and timestamps.

Every important operation must be traceable from founder request to final verified result.

Create a dedicated Security Agent.

The Security Agent must inspect permissions, dangerous commands, secret exposure, unauthorized access, suspicious downloads, unsafe repositories, unexpected network activity, destructive operations, privilege escalation attempts and other security-relevant behavior.

High-risk actions must require explicit founder approval.

Do not implement fake autonomy.

Do not create interface buttons that simulate capabilities which the backend does not actually implement.

If a capability is absent, display:

NOT IMPLEMENTED

If it is incomplete:

PARTIAL

If implementation exists but has not been tested:

IMPLEMENTED — UNVERIFIED

If testing succeeded:

VERIFIED

If all necessary production checks pass:

PRODUCTION READY

The UI must reflect actual backend state.

Do not build the system as a page-by-page wizard that requires the founder to manually progress through artificial pages such as "Page 1 browser," "Page 2 coding," "Page 3 research," etc.

All capabilities must exist as integrated system components inside one unified application.

The founder should be able to ask one natural-language request and allow the Orchestrator to determine which agents, tools, research processes, browser actions, coding operations, local operations, tests, verification processes and integrations are required.

Do not force the founder to manually move from one module to another to complete a single task.

The system itself should coordinate the modules.

The architecture must remain modular internally, but the founder experience must feel like one unified agent.

The system must support a browser-first operating model, local fallback, continuous background execution, persistent memory, persistent task state, real-time UI, tool discovery, open-source integration, coding, research, browser automation, media processing, business workflows, data workflows, API integration, file operations, project management, scheduling, monitoring and future expansion into additional specialized capabilities.

When the founder provides a new platform URL, open-source repository, application URL, software documentation, API documentation or complete platform documentation, the agent must understand what that resource is, inspect its available documentation, determine what functionality it provides, determine how it can be installed or integrated, determine whether it is free/open-source/limited/paid where relevant, inspect compatibility and dependencies, determine how it can contribute to the current project, obtain permission when required, install or integrate it, configure it, test it, verify it, register it in the Tool Registry, register the resulting capabilities in the Capability Registry, record its version and source, connect it to the relevant projects and make it available to future tasks.

Maintain an organized backend repository of installed tools, open-source projects, downloaded source code, models, dependencies, documentation, configurations, artifacts, project resources and synchronized metadata.

The backend must always know:

what is installed,
where it is installed,
what version is installed,
where it came from,
what repository it belongs to,
what license it uses,
what dependencies it requires,
what projects use it,
what capabilities it provides,
whether it is healthy,
when it was last verified,
whether it is outdated,
whether it is currently active,
whether it failed,
whether it has been disabled,
whether an update is available,
what depends upon it,
and how to restore or remove it safely.

The system must synchronize these registries with actual runtime state.

If the database says a tool is ACTIVE but the executable is missing, the system must detect the inconsistency and change the state to an appropriate unhealthy/unverified state rather than trusting the database blindly.

If the system detects software installed outside the agent registry and the software is relevant, it may discover and propose registration after verification.

Create a synchronization engine that periodically and event-drivenly compares:

DATABASE STATE
↔
FILESYSTEM STATE
↔
PROCESS STATE
↔
INSTALLED SOFTWARE STATE
↔
REPOSITORY STATE
↔
MODEL STATE
↔
SERVICE STATE
↔
CAPABILITY STATE

Any discrepancy must be reported and reconciled safely.

Create a continuous system learning and improvement loop.

After each significant task, capture:

what was requested,
what was planned,
what was attempted,
what tools were used,
what worked,
what failed,
what was learned,
what was verified,
what should be reused,
what should not be repeated,
what capability was created,
what capability was improved,
what dependencies changed,
what remains unfinished.

The agent must use this history to improve future planning without silently modifying critical security or system behavior.

The system must support founder-level project continuity.

If the founder returns after hours or days and says:

"Continue the video agent."

the system must inspect the Project Registry, Task Graph, previous executions, pending tasks, failed tasks, blocked tasks, tool registry, capability registry and recent verification results before deciding what "continue" means.

It must not rely only on conversational memory.

The system must be able to resume from the last verified checkpoint.

The agent must be able to stop, pause, resume, cancel and retry tasks while preserving state.

Long-running operations must survive browser disconnection and recover from worker restart where possible.

Every major operation should have checkpoint and rollback information.

The system should be able to explain its current execution state in natural language.

For example:

"I am currently researching compatible open-source video-processing tools. I found three candidates. I have not installed anything yet. One candidate requires local GPU resources, one can run remotely, and one has an incompatible dependency. I am waiting for your permission before installing the compatible candidate."

The agent must never pretend to be working when no backend operation is occurring.

The live UI must be driven by actual events.

The system must never generate fake progress numbers.

If the agent reports 64% progress, that progress must correspond to real task state.

The system must maintain clear separation between:

reasoning,
planning,
execution,
permissions,
state,
memory,
tools,
verification,
security and presentation.

The LLM should make decisions and generate plans.

The runtime must enforce execution reality.

The Permission Engine must enforce authority.

The tools must perform actual operations.

The database must persist actual state.

The Verification Agent must validate results.

The Security Agent must enforce security requirements.

The UI must display actual state.

For example:

LLM:
"I need to install this dependency."

Runtime:
"Permission required."

Permission Engine:
"Permission granted for this project."

Runtime:
"Installation started."

Tool:
"Installation completed."

Runtime:
"Installation result received."

Verification Agent:
"Executable detected, version checked, test executed successfully."

Database:
"Tool status = ACTIVE."

Capability Registry:
"VIDEO_PROCESSING = ACTIVE."

Project Registry:
"Video Agent dependency satisfied."

Only then should the conversational layer report that the capability is active.

The system must include comprehensive acceptance verification.

Do not consider the platform complete merely because the frontend loads.

The final system must demonstrate working voice input, working text input, URL understanding, file understanding, natural-language requirement extraction, intent classification, task planning, research, documentation analysis, GitHub inspection, open-source discovery, tool registry, software inventory, capability registry, project registry, permission engine, approval workflow, browser automation, browser navigation, browser sessions, DOM/structured extraction, screenshots, clicking, typing, downloads, uploads, authentication-aware workflows, local bridge, controlled terminal execution, controlled PowerShell execution, coding agent, code execution sandbox, testing agent, verification agent, persistent memory, knowledge ingestion, scheduler, background workers, 24/7 runtime, heartbeat, crash recovery, retry handling, audit logs, security controls, real-time UI, live task progress, approval notifications, rollback/checkpoints, health monitoring, self-diagnostics, capability discovery, dependency tracking, version tracking, state synchronization, browser/local execution switching, truthful completion reporting, persistent project state, persistent tool state, persistent capability state and independently verifiable task completion.

Every major capability must have a real backend implementation.

Every UI control must connect to actual functionality.

Every task must have persistent state.

Every sensitive operation must be permission-controlled.

Every completed operation must have a verification path.

Every external tool must be registered.

Every installed resource must be tracked.

Every project must have persistent state.

Every failure must be recorded.

Every long-running operation must have monitoring and recovery.

Every important system state must survive browser refresh and, where designed, service restart.

The system must remain extensible so that future capabilities can be added as agents, tools, connectors, skills and modules without rebuilding the core runtime.

Do not treat this specification as a set of separate pages.

Treat the entire specification as ONE unified system.

Do not implement the features as isolated demonstrations.

Connect every component to the central runtime, persistent state, permissions, task engine, tool registry, capability registry, project registry, event system, verification system and UI.

Do not stop after creating the architecture.

Build the actual working implementation.

When implementation is complete, run the actual audit and diagnostics against the built system.

Identify every feature as:

VERIFIED
IMPLEMENTED — UNVERIFIED
PARTIAL
BLOCKED
FAILED
NOT IMPLEMENTED

Then continue implementing missing and incomplete functionality until the system reaches the highest genuinely achievable working state.

Never claim production readiness based only on code generation.

Production readiness must be established through actual execution, testing, verification, security checks, state synchronization, failure handling and real-world workflow testing.

The ultimate operating behavior must be:

When the founder says "Build X," the agent must understand X, inspect the existing system, inspect existing projects, inspect existing capabilities, inspect installed tools, inspect previous work, identify missing components, research appropriate solutions, analyze available open-source resources, inspect documentation, determine architecture, create the required task graph, determine required permissions, ask only when authorization is genuinely required, execute the work using the appropriate agents and tools, use browser execution whenever possible, activate local execution only when necessary and authorized, observe every important operation, recover from errors, test the result, independently verify the result, register new tools and capabilities, update project state, update memory, update dependencies, create checkpoints, record audit information, continue all remaining tasks, monitor long-running work and report only the actual verified state.

Before every major action, the system must internally establish:

WHAT IS THE CURRENT VERIFIED STATE?

WHAT MUST CHANGE?

WHAT CAPABILITY IS REQUIRED?

WHAT TOOL OR AGENT SHOULD PERFORM THE CHANGE?

WHAT PERMISSION IS REQUIRED?

WHAT IS THE SAFEST AUTHORIZED EXECUTION METHOD?

HOW WILL THE RESULT BE VERIFIED?

WHAT STATE MUST BE UPDATED AFTERWARD?

Then execute the operation, observe the result, verify it, record it and continue.

The database/runtime, not the language model, is the authoritative source of execution state.

The entire platform must be built as a real, persistent, permission-controlled, browser-first, locally extensible, continuously running, research-capable, coding-capable, automation-capable, self-monitoring and independently verifiable autonomous agent operating system for the founder.
