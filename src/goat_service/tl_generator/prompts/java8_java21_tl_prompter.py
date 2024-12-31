from langchain.prompts.chat import SystemMessagePromptTemplate

from src.goat_service.tl_generator.prompts.tl_prompter import (
    TLPrompter,
)
from src.goat_service.utils.operation_applier import (
    OP_USAGE,
)

system_message = SystemMessagePromptTemplate.from_template(
    """\
You are a senior Java programmer. 
Your task is to convert a Java 8 project to a Java 21 project and to upgrade spring boot to version 3.3.
That means doing the following:
1. change java version to 21
2. change spring boot version to 3.3
3. search for javax imports in all files and change them to jakarta imports
4. change snake yaml to jackson yaml.
  - when changing to jackson, do not forget to include the following imports:
    - import com.fasterxml.jackson.databind.ObjectMapper;
    - import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
    - import org.springframework.http.MediaType;
  - and in build.gradle add as dependency: implementation 'com.fasterxml.jackson.dataformat:jackson-dataformat-yaml'
5. change the @RequestMapping annotations to @GetMapping, @PostMapping, @PutMapping or @DeleteMapping.

{OP_USAGE}

"""
)

system_message = system_message.format(
    OP_USAGE=OP_USAGE,
)


class Java8ToJava21TLPrompter(TLPrompter):
    system_message = system_message
