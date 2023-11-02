from enum import Enum
from typing import List, Literal, get_args


class ActorJobStatus(str, Enum):
    """Available statuses for actor jobs (runs or builds)."""

    #: Actor job initialized but not started yet
    READY = 'READY'
    #: Actor job in progress
    RUNNING = 'RUNNING'
    #: Actor job finished successfully
    SUCCEEDED = 'SUCCEEDED'
    #: Actor job or build failed
    FAILED = 'FAILED'
    #: Actor job currently timing out
    TIMING_OUT = 'TIMING-OUT'
    #: Actor job timed out
    TIMED_OUT = 'TIMED-OUT'
    #: Actor job currently being aborted by user
    ABORTING = 'ABORTING'
    #: Actor job aborted by user
    ABORTED = 'ABORTED'

    @property
    def _is_terminal(self) -> bool:
        """Whether this actor job status is terminal."""
        return self in (ActorJobStatus.SUCCEEDED, ActorJobStatus.FAILED, ActorJobStatus.TIMED_OUT, ActorJobStatus.ABORTED)


class ActorSourceType(str, Enum):
    """Available source types for actors."""

    #: Actor source code is comprised of multiple files
    SOURCE_FILES = 'SOURCE_FILES'
    #: Actor source code is cloned from a Git repository
    GIT_REPO = 'GIT_REPO'
    #: Actor source code is downloaded using a tarball or Zip file
    TARBALL = 'TARBALL'
    #: Actor source code is taken from a GitHub Gist
    GITHUB_GIST = 'GITHUB_GIST'


class ActorEventTypes(str, Enum):
    """Possible values of actor event type."""

    #: Info about resource usage of the actor
    SYSTEM_INFO = 'systemInfo'
    #: Sent when the actor is about to migrate
    MIGRATING = 'migrating'
    #: Sent when the actor should persist its state (every minute or when migrating)
    PERSIST_STATE = 'persistState'
    #: Sent when the actor is aborting
    ABORTING = 'aborting'


class ActorEnvVars(str, Enum):
    """Possible Apify-specific environment variables prefixed with "ACTOR_"."""

    # TODO: document these

    #: BUILD_ID
    BUILD_ID = 'ACTOR_BUILD_ID'
    #: BUILD_NUMBER
    BUILD_NUMBER = 'ACTOR_BUILD_NUMBER'
    #: DEFAULT_DATASET_ID
    DEFAULT_DATASET_ID = 'ACTOR_DEFAULT_DATASET_ID'
    #: DEFAULT_KEY_VALUE_STORE_ID
    DEFAULT_KEY_VALUE_STORE_ID = 'ACTOR_DEFAULT_KEY_VALUE_STORE_ID'
    #: DEFAULT_REQUEST_QUEUE_ID
    DEFAULT_REQUEST_QUEUE_ID = 'ACTOR_DEFAULT_REQUEST_QUEUE_ID'
    #: EVENTS_WEBSOCKET_URL
    EVENTS_WEBSOCKET_URL = 'ACTOR_EVENTS_WEBSOCKET_URL'
    #: ID
    ID = 'ACTOR_ID'
    #: INPUT_KEY
    INPUT_KEY = 'ACTOR_INPUT_KEY'
    #: MAX_PAID_DATASET_ITEMS
    MAX_PAID_DATASET_ITEMS = 'ACTOR_MAX_PAID_DATASET_ITEMS'
    #: MEMORY_MBYTES
    MEMORY_MBYTES = 'ACTOR_MEMORY_MBYTES'
    #: RUN_ID
    RUN_ID = 'ACTOR_RUN_ID'
    #: STARTED_AT
    STARTED_AT = 'ACTOR_STARTED_AT'
    #: TASK_ID
    TASK_ID = 'ACTOR_TASK_ID'
    #: TIMEOUT_AT
    TIMEOUT_AT = 'ACTOR_TIMEOUT_AT'
    #: WEB_SERVER_PORT
    WEB_SERVER_PORT = 'ACTOR_WEB_SERVER_PORT'
    #: WEB_SERVER_URL
    WEB_SERVER_URL = 'ACTOR_WEB_SERVER_URL'


class ApifyEnvVars(str, Enum):
    """Possible Apify-specific environment variables prefixed with "APIFY_"."""

    # TODO: document these

    #: API_BASE_URL
    API_BASE_URL = 'APIFY_API_BASE_URL'
    #: API_PUBLIC_BASE_URL
    API_PUBLIC_BASE_URL = 'APIFY_API_PUBLIC_BASE_URL'
    #: CHROME_EXECUTABLE_PATH
    CHROME_EXECUTABLE_PATH = 'APIFY_CHROME_EXECUTABLE_PATH'
    #: DEDICATED_CPUS
    DEDICATED_CPUS = 'APIFY_DEDICATED_CPUS'
    #: DEFAULT_BROWSER_PATH
    DEFAULT_BROWSER_PATH = 'APIFY_DEFAULT_BROWSER_PATH'
    #: DISABLE_BROWSER_SANDBOX
    DISABLE_BROWSER_SANDBOX = 'APIFY_DISABLE_BROWSER_SANDBOX'
    #: DISABLE_OUTDATED_WARNING
    DISABLE_OUTDATED_WARNING = 'APIFY_DISABLE_OUTDATED_WARNING'
    #: FACT
    FACT = 'APIFY_FACT'
    #: HEADLESS
    HEADLESS = 'APIFY_HEADLESS'
    #: INPUT_SECRETS_PRIVATE_KEY_FILE
    INPUT_SECRETS_PRIVATE_KEY_FILE = 'APIFY_INPUT_SECRETS_PRIVATE_KEY_FILE'
    #: INPUT_SECRETS_PRIVATE_KEY_PASSPHRASE
    INPUT_SECRETS_PRIVATE_KEY_PASSPHRASE = 'APIFY_INPUT_SECRETS_PRIVATE_KEY_PASSPHRASE'
    #: IS_AT_HOME
    IS_AT_HOME = 'APIFY_IS_AT_HOME'
    #: LOCAL_STORAGE_DIR
    LOCAL_STORAGE_DIR = 'APIFY_LOCAL_STORAGE_DIR'
    #: LOG_FORMAT
    LOG_FORMAT = 'APIFY_LOG_FORMAT'
    #: LOG_LEVEL
    LOG_LEVEL = 'APIFY_LOG_LEVEL'
    #: MAX_USED_CPU_RATIO
    MAX_USED_CPU_RATIO = 'APIFY_MAX_USED_CPU_RATIO'
    #: META_ORIGIN
    META_ORIGIN = 'APIFY_META_ORIGIN'
    #: METAMORPH_AFTER_SLEEP_MILLIS
    METAMORPH_AFTER_SLEEP_MILLIS = 'APIFY_METAMORPH_AFTER_SLEEP_MILLIS'
    #: PERSIST_STATE_INTERVAL_MILLIS
    PERSIST_STATE_INTERVAL_MILLIS = 'APIFY_PERSIST_STATE_INTERVAL_MILLIS'
    #: PERSIST_STORAGE
    PERSIST_STORAGE = 'APIFY_PERSIST_STORAGE'
    #: PROXY_HOSTNAME
    PROXY_HOSTNAME = 'APIFY_PROXY_HOSTNAME'
    #: PROXY_PASSWORD
    PROXY_PASSWORD = 'APIFY_PROXY_PASSWORD'
    #: PROXY_PORT
    PROXY_PORT = 'APIFY_PROXY_PORT'
    #: PROXY_STATUS_URL
    PROXY_STATUS_URL = 'APIFY_PROXY_STATUS_URL'
    #: PURGE_ON_START
    PURGE_ON_START = 'APIFY_PURGE_ON_START'
    #: SDK_LATEST_VERSION
    SDK_LATEST_VERSION = 'APIFY_SDK_LATEST_VERSION'
    #: SYSTEM_INFO_INTERVAL_MILLIS
    SYSTEM_INFO_INTERVAL_MILLIS = 'APIFY_SYSTEM_INFO_INTERVAL_MILLIS'
    #: TOKEN
    TOKEN = 'APIFY_TOKEN'
    #: USER_ID
    USER_ID = 'APIFY_USER_ID'
    #: WORKFLOW_KEY
    WORKFLOW_KEY = 'APIFY_WORKFLOW_KEY'
    #: XVFB
    XVFB = 'APIFY_XVFB'

    # Replaced by ActorEnvVars, kept for backward compatibility:
    #: ACTOR_BUILD_ID
    ACTOR_BUILD_ID = 'APIFY_ACTOR_BUILD_ID'
    #: ACTOR_BUILD_NUMBER
    ACTOR_BUILD_NUMBER = 'APIFY_ACTOR_BUILD_NUMBER'
    #: ACTOR_EVENTS_WS_URL
    ACTOR_EVENTS_WS_URL = 'APIFY_ACTOR_EVENTS_WS_URL'
    #: ACTOR_ID
    ACTOR_ID = 'APIFY_ACTOR_ID'
    #: ACTOR_RUN_ID
    ACTOR_RUN_ID = 'APIFY_ACTOR_RUN_ID'
    #: ACTOR_TASK_ID
    ACTOR_TASK_ID = 'APIFY_ACTOR_TASK_ID'
    #: CONTAINER_PORT
    CONTAINER_PORT = 'APIFY_CONTAINER_PORT'
    #: CONTAINER_URL
    CONTAINER_URL = 'APIFY_CONTAINER_URL'
    #: DEFAULT_DATASET_ID
    DEFAULT_DATASET_ID = 'APIFY_DEFAULT_DATASET_ID'
    #: DEFAULT_KEY_VALUE_STORE_ID
    DEFAULT_KEY_VALUE_STORE_ID = 'APIFY_DEFAULT_KEY_VALUE_STORE_ID'
    #: DEFAULT_REQUEST_QUEUE_ID
    DEFAULT_REQUEST_QUEUE_ID = 'APIFY_DEFAULT_REQUEST_QUEUE_ID'
    #: INPUT_KEY
    INPUT_KEY = 'APIFY_INPUT_KEY'
    #: MEMORY_MBYTES
    MEMORY_MBYTES = 'APIFY_MEMORY_MBYTES'
    #: STARTED_AT
    STARTED_AT = 'APIFY_STARTED_AT'
    #: TIMEOUT_AT
    TIMEOUT_AT = 'APIFY_TIMEOUT_AT'

    # Deprecated, kept for backward compatibility:
    #: ACT_ID
    ACT_ID = 'APIFY_ACT_ID'
    #: ACT_RUN_ID
    ACT_RUN_ID = 'APIFY_ACT_RUN_ID'


class ActorExitCodes(int, Enum):
    """Usual actor exit codes."""

    #: The actor finished successfully
    SUCCESS = 0

    #: The main function of the actor threw an Exception
    ERROR_USER_FUNCTION_THREW = 91


class WebhookEventType(str, Enum):
    """Events that can trigger a webhook."""

    #: The actor run was created
    ACTOR_RUN_CREATED = 'ACTOR.RUN.CREATED'
    #: The actor run has succeeded
    ACTOR_RUN_SUCCEEDED = 'ACTOR.RUN.SUCCEEDED'
    #: The actor run has failed
    ACTOR_RUN_FAILED = 'ACTOR.RUN.FAILED'
    #: The actor run has timed out
    ACTOR_RUN_TIMED_OUT = 'ACTOR.RUN.TIMED_OUT'
    #: The actor run was aborted
    ACTOR_RUN_ABORTED = 'ACTOR.RUN.ABORTED'
    #: The actor run was resurrected
    ACTOR_RUN_RESURRECTED = 'ACTOR.RUN.RESURRECTED'

    #: The actor build was created
    ACTOR_BUILD_CREATED = 'ACTOR.BUILD.CREATED'
    #: The actor build has succeeded
    ACTOR_BUILD_SUCCEEDED = 'ACTOR.BUILD.SUCCEEDED'
    #: The actor build has failed
    ACTOR_BUILD_FAILED = 'ACTOR.BUILD.FAILED'
    #: The actor build has timed out
    ACTOR_BUILD_TIMED_OUT = 'ACTOR.BUILD.TIMED_OUT'
    #: The actor build was aborted
    ACTOR_BUILD_ABORTED = 'ACTOR.BUILD.ABORTED'


class MetaOrigin(str, Enum):
    """Possible origins for actor runs, i.e. how were the jobs started."""

    #: Job started from Developer console in Source section of actor
    DEVELOPMENT = 'DEVELOPMENT'
    #: Job started from other place on the website (either console or task detail page)
    WEB = 'WEB'
    #: Job started through API
    API = 'API'
    #: Job started through Scheduler
    SCHEDULER = 'SCHEDULER'
    #: Job started through test actor page
    TEST = 'TEST'
    #: Job started by the webhook
    WEBHOOK = 'WEBHOOK'
    #: Job started by another actor run
    ACTOR = 'ACTOR'


INTEGER_ENV_VARS_TYPE = Literal[
    # Actor env vars
    ActorEnvVars.MAX_PAID_DATASET_ITEMS,
    ActorEnvVars.MEMORY_MBYTES,
    ActorEnvVars.WEB_SERVER_PORT,
    # Apify env vars
    ApifyEnvVars.CONTAINER_PORT,
    ApifyEnvVars.DEDICATED_CPUS,
    ApifyEnvVars.LOG_LEVEL,
    ApifyEnvVars.MEMORY_MBYTES,
    ApifyEnvVars.METAMORPH_AFTER_SLEEP_MILLIS,
    ApifyEnvVars.PERSIST_STATE_INTERVAL_MILLIS,
    ApifyEnvVars.PROXY_PORT,
    ApifyEnvVars.SYSTEM_INFO_INTERVAL_MILLIS,
]

INTEGER_ENV_VARS: List[INTEGER_ENV_VARS_TYPE] = list(get_args(INTEGER_ENV_VARS_TYPE))

FLOAT_ENV_VARS_TYPE = Literal[
    ApifyEnvVars.MAX_USED_CPU_RATIO,
]

FLOAT_ENV_VARS: List[FLOAT_ENV_VARS_TYPE] = list(get_args(FLOAT_ENV_VARS_TYPE))

BOOL_ENV_VARS_TYPE = Literal[
    ApifyEnvVars.DISABLE_BROWSER_SANDBOX,
    ApifyEnvVars.DISABLE_OUTDATED_WARNING,
    ApifyEnvVars.HEADLESS,
    ApifyEnvVars.IS_AT_HOME,
    ApifyEnvVars.PERSIST_STORAGE,
    ApifyEnvVars.PURGE_ON_START,
    ApifyEnvVars.XVFB,
]

BOOL_ENV_VARS: List[BOOL_ENV_VARS_TYPE] = list(get_args(BOOL_ENV_VARS_TYPE))

DATETIME_ENV_VARS_TYPE = Literal[
    # Actor env vars
    ActorEnvVars.STARTED_AT,
    ActorEnvVars.TIMEOUT_AT,
    # Apify env vars
    ApifyEnvVars.STARTED_AT,
    ApifyEnvVars.TIMEOUT_AT,
]

DATETIME_ENV_VARS: List[DATETIME_ENV_VARS_TYPE] = list(get_args(DATETIME_ENV_VARS_TYPE))

STRING_ENV_VARS_TYPE = Literal[
    # Actor env vars
    ActorEnvVars.BUILD_ID,
    ActorEnvVars.BUILD_NUMBER,
    ActorEnvVars.DEFAULT_DATASET_ID,
    ActorEnvVars.DEFAULT_KEY_VALUE_STORE_ID,
    ActorEnvVars.DEFAULT_REQUEST_QUEUE_ID,
    ActorEnvVars.EVENTS_WEBSOCKET_URL,
    ActorEnvVars.ID,
    ActorEnvVars.INPUT_KEY,
    ActorEnvVars.RUN_ID,
    ActorEnvVars.TASK_ID,
    ActorEnvVars.WEB_SERVER_URL,
    # Apify env vars
    ApifyEnvVars.ACT_ID,
    ApifyEnvVars.ACT_RUN_ID,
    ApifyEnvVars.ACTOR_BUILD_ID,
    ApifyEnvVars.ACTOR_BUILD_NUMBER,
    ApifyEnvVars.ACTOR_EVENTS_WS_URL,
    ApifyEnvVars.ACTOR_ID,
    ApifyEnvVars.ACTOR_RUN_ID,
    ApifyEnvVars.ACTOR_TASK_ID,
    ApifyEnvVars.API_BASE_URL,
    ApifyEnvVars.API_PUBLIC_BASE_URL,
    ApifyEnvVars.CHROME_EXECUTABLE_PATH,
    ApifyEnvVars.CONTAINER_URL,
    ApifyEnvVars.DEFAULT_BROWSER_PATH,
    ApifyEnvVars.DEFAULT_DATASET_ID,
    ApifyEnvVars.DEFAULT_KEY_VALUE_STORE_ID,
    ApifyEnvVars.DEFAULT_REQUEST_QUEUE_ID,
    ApifyEnvVars.FACT,
    ApifyEnvVars.INPUT_KEY,
    ApifyEnvVars.INPUT_SECRETS_PRIVATE_KEY_FILE,
    ApifyEnvVars.INPUT_SECRETS_PRIVATE_KEY_PASSPHRASE,
    ApifyEnvVars.LOCAL_STORAGE_DIR,
    ApifyEnvVars.LOG_FORMAT,
    ApifyEnvVars.META_ORIGIN,
    ApifyEnvVars.PROXY_HOSTNAME,
    ApifyEnvVars.PROXY_PASSWORD,
    ApifyEnvVars.PROXY_STATUS_URL,
    ApifyEnvVars.SDK_LATEST_VERSION,
    ApifyEnvVars.TOKEN,
    ApifyEnvVars.USER_ID,
    ApifyEnvVars.WORKFLOW_KEY,
]

STRING_ENV_VARS: List[STRING_ENV_VARS_TYPE] = list(get_args(STRING_ENV_VARS_TYPE))
