using API_Gateway.Models.Project;

namespace API_Gateway.Services;

public class BackupService : IBackupService
{
    private readonly string? backupBaseDir;
    private readonly ILogger<BackupService> logger;

    public BackupService(IConfiguration configuration, ILogger<BackupService> logger)
    {
        this.logger = logger;
        backupBaseDir = configuration.GetValue<string?>("Backup:BackupBaseDir");
        if (backupBaseDir == null)
        {
            logger.LogWarning("Backup Failed: Backup base directory is not set.");
        }
    }

    public async Task Backup(string content, string traceId, string workflowName, string folderName, string id = "")
    {
        DateTime startTime = DateTime.Now;
        string? dirPath = CreateBackupDir(traceId, workflowName, folderName, id);
        if (dirPath == null)
        {
            return;
        }

        // save content into dirPath/content.txt
        await File.WriteAllTextAsync(Path.Combine(dirPath, "content.txt"), content);

        DateTime endTime = DateTime.Now;
        logger.LogInformation(
            $"Backup of folderName {folderName} with id {id} completed in {(endTime - startTime).TotalSeconds} seconds."
        );
    }

    public async Task Backup(
        CodeProject project,
        string traceId,
        string workflowName,
        string folderName,
        string id = ""
    )
    {
        DateTime startTime = DateTime.Now;
        string? dirPath = CreateBackupDir(traceId, workflowName, folderName, id);
        if (dirPath == null)
        {
            return;
        }

        List<Task> tasks = [];
        // save files into dirPath/files
        string filesDirPath = Path.Combine(dirPath, "files");
        Directory.CreateDirectory(filesDirPath);
        foreach (var file in project.Files)
        {
            // filename contains directories aswell
            string directoryName = Path.GetDirectoryName(file.FileName) ?? string.Empty;
            Directory.CreateDirectory(Path.Combine(filesDirPath, directoryName));
            tasks.Add(File.WriteAllTextAsync(Path.Combine(filesDirPath, file.FileName), file.SourceCode));
        }
        // save reference files
        string referenceFilesDirPath = Path.Combine(dirPath, "reference_files");
        Directory.CreateDirectory(referenceFilesDirPath);
        foreach (var file in project.ReferenceFiles)
        {
            // filename contains directories aswell
            string directoryName = Path.GetDirectoryName(file.FileName) ?? string.Empty;
            Directory.CreateDirectory(Path.Combine(referenceFilesDirPath, directoryName));
            tasks.Add(File.WriteAllTextAsync(Path.Combine(referenceFilesDirPath, file.FileName), file.SourceCode));
        }
        await Task.WhenAll(tasks);

        DateTime endTime = DateTime.Now;
        logger.LogInformation(
            $"Backup of folderName {folderName} with id {id} and language {project.SourceLanguage} completed in {(endTime - startTime).TotalSeconds} seconds."
        );
    }

    private string? CreateBackupDir(string traceId, string workflowName, string folderName, string id)
    {
        if (backupBaseDir == null)
        {
            logger.LogWarning("Backup Failed: Backup base directory is not set.");
            return null;
        }
        string date = DateTime.Now.ToString("yyyy-MM-dd");
        string time = DateTime.Now.ToString("HH-mm-ss");
        string guid = Guid.NewGuid().ToString("N");
        string time_guid = $"{time}_{guid}";
        if (id != "")
        {
            time_guid = $"{id}_{time_guid}";
        }

        // backup dir example: /mnt/gs-vault/date/trace-id/workflow/time_guid
        string dirPath = Path.Combine(backupBaseDir, date, traceId, workflowName, folderName, time_guid);
        Directory.CreateDirectory(dirPath);
        return dirPath;
    }

    public async Task Backup(List<CodeProject> projects, string traceId, string workflowName, string folderName)
    {
        if (backupBaseDir == null)
        {
            logger.LogWarning("Backup Failed: Backup base directory is not set.");
            return;
        }
        DateTime startTime = DateTime.Now;
        // use id to differentiate between projects
        List<Task> tasks = [];
        for (int i = 0; i < projects.Count; i++)
        {
            tasks.Add(Backup(projects[i], traceId, workflowName, folderName, i.ToString()));
        }
        await Task.WhenAll(tasks);
        DateTime endTime = DateTime.Now;
        logger.LogInformation(
            $"Backup of folderName {folderName} completed in {(endTime - startTime).TotalSeconds} seconds."
        );
    }
}
