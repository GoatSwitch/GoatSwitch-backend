
namespace API_Gateway.Services.Exceptions
{
    public class GSBaseException : Exception
    {
        public static readonly string SupportMessage = " If the problem persists, please contact support at hello@goatswitch.ai.";
        public virtual string UserMessage { get; } = "Unexpected error occurred. Please try again. "
            + SupportMessage;
        public static string HighDemandMessage { get; } = "Request failed due to high demand. Please try again in 30 seconds."
            + SupportMessage;
        public static string ContentTooLongMessage { get; } = "Request failed due to the content being too long. Please remove some files and try again."
            + SupportMessage;
        public GSBaseException(string message) : base(message)
        {
            this.UserMessage = GetSpecialExceptionMessage(message);
        }
        public string GetSpecialExceptionMessage(string error)
        {
            if (error.Contains("token rate limit"))
            {
                return HighDemandMessage;
            }
            else if (error.Contains("string_above_max_length"))
            {
                return ContentTooLongMessage;
            }
            else
            {
                return UserMessage;
            }
        }
    }
    public class TLGException : GSBaseException
    {
        public override string UserMessage { get; } = "Failed to generate translations, please try again. "
            + SupportMessage;
        public TLGException(string message) : base(message)
        {
            this.UserMessage = GetSpecialExceptionMessage(message);
        }
    }
    public class PlanGException : GSBaseException
    {
        public override string UserMessage { get; } = "Failed to generate plan, please try again. "
            + SupportMessage;
        public PlanGException(string message) : base(message)
        {
            this.UserMessage = GetSpecialExceptionMessage(message);
        }
    }
    public class UTGException : GSBaseException
    {
        public override string UserMessage { get; } = "Failed to generate tests, please try again. "
            + SupportMessage;
        public UTGException(string message) : base(message)
        {
            this.UserMessage = GetSpecialExceptionMessage(message);
        }
    }
    public class TLPException : GSBaseException
    {
        public override string UserMessage { get; } = "Failed to pick translations, please fix the code and try again. "
            + SupportMessage;
        public TLPException(string message) : base(message)
        {
            this.UserMessage = GetSpecialExceptionMessage(message);
        }
    }
    public class UTPException : GSBaseException
    {
        public override string UserMessage { get; } = "Failed to pick tests, please fix the code and try again. "
            + SupportMessage;
        public UTPException(string message) : base(message)
        {
            this.UserMessage = GetSpecialExceptionMessage(message);
        }
    }
    public class SourceCompileException : GSBaseException
    {
        public override string UserMessage { get; } = "Failed to compile source project. "
            + SupportMessage;
        public SourceCompileException(string message) : base(message)
        {
            this.UserMessage = GetSpecialExceptionMessage(message);
        }
    }
    public class HighDemandException : GSBaseException
    {
        public override string UserMessage { get; } = "Request failed due to high demand. Please try again in 30 seconds."
            + SupportMessage;
        public HighDemandException(string message) : base(message)
        {
            this.UserMessage = GetSpecialExceptionMessage(message);
        }
    }
    public class ContentTooLongException : GSBaseException
    {
        public override string UserMessage { get; } = "Request failed due to the content being too long. Please remove some files and try again."
            + SupportMessage;
        public ContentTooLongException(string message) : base(message)
        {
            this.UserMessage = GetSpecialExceptionMessage(message);
        }
    }
}