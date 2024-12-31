import logging

from gs_common.CodeProject import CodeFile, CodeProject
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts.chat import SystemMessagePromptTemplate
from pydantic import BaseModel, field_validator

from src.goat_service.ut_generator.prompts.ut_prompter import UTPrompter


class JUnitFile(CodeFile):
    @field_validator("source_code")
    def must_contain_test_methods(cls, v):
        if v.count("@Test") < 2:
            raise ValueError("Must contain multiple @Test methods")
        return v


class JunitProjectStepByStepOutput(BaseModel):
    relevant_classes_for_testing: list[str]
    top_relevant_classes_for_testing: list[str]
    top_relevant_classes_for_testing_with_public_methods: dict[str, list[str]]
    # dict of file names and list of public methods
    top_relevant_classes_for_testing_with_top_relevant_public_methods: dict[
        str, list[str]
    ]
    # dict of file names and dict of public methods and test cases
    top_relevant_classes_for_testing_with_top_relevant_public_methods_with_test_case_names: dict[
        str, dict[str, list[str]]
    ]
    junit_files: list[JUnitFile]

    # files cannot be empty
    @field_validator("junit_files")
    def junit_files_must_not_be_empty(cls, v):
        if len(v) == 0:
            raise ValueError("junit_files must not be empty")
        return v


output_parser = PydanticOutputParser(pydantic_object=JunitProjectStepByStepOutput)

system_message = SystemMessagePromptTemplate.from_template(
    """\
You are a experienced JUnit Java unit test engineer.
Your task is to generate JUnit Test classes for java code classes.
The incoming code will be in Java 21.
All generated Test classes must be executable with the JUnit framework.
                                                                  
The rulebook for your position is as follows:
- Your answer must be in JSON form structured like this: {json_output_schema}
- Your answer must not include any additional text.
- Use the arrange-act-assert pattern for your tests.
- One test method should contain one test case.
- Always make sure the unittests have high coverage and diverse test cases.
- It is of utmost importance that the unittests fully implemented without any TODOs or placeholders, because these exact unittests will be used in production.
- You may not generate any test methods without assertions.
- Do not test abstract classes.
- Do not test private methods.
- Do not test methods that have no access modifier. They are private by default.
- Only test public or protected methods.
- Do not test any exceptions.
- Do not test whether a method is throwing an exception.
- Use import static org.junit.jupiter.api.Assertions.*;

To make your task easier, you will generate the test files step by step:
1. Go through the list of CodeFiles and identify all classes that are relevant and eligible for testing (must be public or internal). 
Write the full class definition (access modifiers and name as one string) to a list named relevant_classes_for_testing.
It is a best practice to test at least one controller and one entity class.
2. Go through the list of relevant_classes_for_testing 
and pick the top {top_n_classes} classes that are most relevant for testing.
Do not pick any classes that are private or abstract. Write the class names to a list named top_relevant_classes_for_testing.
3. Go through the list of top_relevant_classes_for_testing 
and for each class, extract all public and internal methods and constructors including their full definitions (method signatures and parameters). 
Write the full definitions to a list named top_relevant_classes_for_testing_with_public_methods.
4. Go through the list of top_relevant_classes_for_testing_with_public_methods
and for each class, identify the top {top_n_methods} public methods that are most relevant for testing (highest code coverage). 
Do not pick any methods that are private or do not have any access modifier. 
Write the method names to a list named top_relevant_classes_for_testing_with_top_relevant_public_methods.
5. For each class in top_relevant_classes_for_testing_with_top_relevant_public_methods, 
define {top_n_cases} potential test case names to a list named top_relevant_classes_for_testing_with_top_relevant_public_methods_with_test_case_names. 
Remember to not make any test cases that test exceptions.
As a best practice, do not test the controller for empty repositories or to check the links.
6. Finally, generate one JUnit Test class (CodeFile) for each file in top_relevant_classes_for_testing_with_top_relevant_public_methods_with_test_case_names. Each CodeFile in the output json must contain:
    - A file_name property with the path of the file (e.g. src/test/java/com/example/MyClassTest.java)
    - A source_code property with the source code of the file (the source_code is encoded as a string in the json but can contain any valid java code)
    - The source_code string must contain one test method for each test case in top_relevant_classes_for_testing_with_top_relevant_public_methods_with_test_case_names
    - You must import the main package of the class you are testing, e.g. package com.example;
    - The test methods must be named after the test case names
    - The test methods must be decorated with the @Test attribute
    - The test methods must be implemented with the arrange-act-assert pattern
    - The test methods must not be empty or contain any TODOs or placeholders
    - The test methods must contain at least one assertion

In the following you are given all filepaths and sourcecodes of a java project in json form.
Please generate multiple JUnit tests adhering to the above rules.
"""
)
system_message = system_message.format(
    json_output_schema=output_parser.get_format_instructions(),
    top_n_classes=1,
    top_n_methods=2,
    top_n_cases=10,
)

task_template = """\
Your task is slightly different now.
Your colleague will refactor the code based on this user requirement:
```Requirement
{instruction}
```

The refactoring will not change any interfaces or method signatures.
Think about which parts of the code are most likely to be affected by the refactoring. 
These are the most_relevant_classes_for_testing and most_relevant_methods_for_testing.

Example:
When migrating from hql to criteria-api, the hql queries will be replaced by criteria queries in the Repository classes. 
Therefore, the Repository classes are most likely to be affected by the refactoring. 
Therefore, you should focus on testing the Repository classes and their methods.
When testing the Repository classes, use actual tests with @SpringBootTest annotation instead of simple mocks.
Use a setUp method to fill the repository with multiple test data before each test. 
The @SpringBootTest annotation will create a new application context for each test method. Do not use the @DataJpaTest annotation, do not use the @Transactional annotation.
Also do not delete the test data at the start of setUp, like with .deleteAll(). This is not necessary.
You must set the Ids directly in the test data to avoid any issues with the auto-generated Ids.
Be aware of lower and upper case issues in the queries. You should only use lower case search strings in the queries.
Do not test the branchNetworkId parameter in the queries. This is not necessary. Do not create empty test methods for this either.


The code will work exactly the same after the refactoring.
Your task is to generate JUnit tests that make sure that the refactored code still works as expected.
Do not write only trivial tests that check null or empty values.
Your tests will be executed with the old and the refactored code.
Please generate JUnit tests for {top_n_classes} classes with {top_n_cases} test cases.
"""


class JUnitUTImprovePrompter(UTPrompter):
    system_message = system_message
    examples = []
    output_parser: PydanticOutputParser = output_parser

    def get_question(self) -> str:
        global task_template
        task = task_template.format(
            instruction=self.instruction,
            top_n_classes=1,
            top_n_methods=2,
            top_n_cases=6,
        )
        logging.info("Task: " + task)

        q = f"Source project:\n{self.source_project.model_dump_json()}"
        q += f"\n\n\nTask:\n{task}"
        return q

    def convert_to_code_project(self, generation: str) -> tuple[CodeProject, bool]:
        stepbystep_output: JunitProjectStepByStepOutput = self.output_parser.parse(
            generation
        )

        # make a codeproject from the junit files
        parsed = CodeProject(
            files=stepbystep_output.junit_files,
            display_name="junit_unittests",
            language="java8",
        )
        # change the file paths from src/test to src/GSTests
        for file in parsed.files:
            file.file_name = file.file_name.replace("src/test", "src/GSTests")
        # add build.gradle file
        build_gradle_file = self.source_project.get_file("build.gradle")
        parsed.files.append(build_gradle_file)
        # log all filenames
        logging.info(
            f"utgen junit project filenames: {[ file.file_name for file in parsed.files ]}"
        )

        return parsed, True
