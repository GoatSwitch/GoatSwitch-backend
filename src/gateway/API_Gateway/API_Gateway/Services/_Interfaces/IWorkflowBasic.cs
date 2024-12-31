using API_Gateway.Models.Project;
using API_Gateway.Models.UTGenerator;

namespace API_Gateway.Services
{
    public interface IWorkflowBasic
    {
        public Task Run(CodeProject sourceProject, string targetLanguage);
    }
}
