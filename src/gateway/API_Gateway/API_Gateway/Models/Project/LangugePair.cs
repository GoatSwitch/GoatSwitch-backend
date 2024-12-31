namespace API_Gateway.Models.Project;

public class LanguagePair
{
    public string SourceLanguage { get; set; }
    public string TargetLanguage { get; set; }

    public LanguagePair(string sourceLanguage, string targetLanguage)
    {
        this.SourceLanguage = sourceLanguage;
        this.TargetLanguage = targetLanguage;
    }
}
