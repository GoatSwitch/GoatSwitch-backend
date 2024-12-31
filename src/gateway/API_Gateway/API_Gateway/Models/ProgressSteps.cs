namespace API_Gateway.Models.Workflow;

public static class WSteps
{
    public static readonly string KEY_STEP1 = "generate_unittests";
    public static readonly string KEY_STEP2 = "translate";
    public static readonly string KEY_STEP3 = "validate";
}

public static class WStates
{
    public static readonly string STATE_DEFAULT = "default";
    public static readonly string STATE_PENDING = "pending";
    public static readonly string STATE_COMPLETED = "completed";
    public static readonly string STATE_INPROGRESS = "in_progress";
    public static readonly string STATE_ERROR = "error";
}
