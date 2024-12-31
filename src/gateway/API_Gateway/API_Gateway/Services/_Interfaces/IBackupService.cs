using API_Gateway.Models.Project;

namespace API_Gateway.Services;

public interface IBackupService
{
    Task Backup(string content, string traceId, string workflowName, string folderName, string id = "");
    Task Backup(CodeProject project, string traceId, string workflowName, string folderName, string id = "");
    Task Backup(List<CodeProject> projects, string traceId, string workflowName, string folderName);
}
