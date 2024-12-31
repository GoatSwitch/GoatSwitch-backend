import logging

from gs_common.CodeProject import CodeFile, CodeProject
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts.chat import SystemMessagePromptTemplate
from pydantic import BaseModel, field_validator

from src.goat_service.ut_generator.prompts.ut_prompter import UTPrompter


class NUnitFile(CodeFile):
    @field_validator("source_code")
    def must_contain_test_methods(cls, v):
        if v.count("[Test]") < 2:
            raise ValueError("Must contain multiple [Test] methods")
        return v


class NunitProjectStepByStepOutput(BaseModel):
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
    nunit_files: list[NUnitFile]

    # files cannot be empty
    @field_validator("nunit_files")
    def nunit_files_must_not_be_empty(cls, v):
        if len(v) == 0:
            raise ValueError("nunit_files must not be empty")
        return v


output_parser = PydanticOutputParser(pydantic_object=NunitProjectStepByStepOutput)

system_message = SystemMessagePromptTemplate.from_template(
    """\
You work at DotNetConvert.inc as a .NET Unittest Engineer.
Your task is to generate NUnit Test classes for .Net code classes.
The incoming code can be in .Net Framework or .Net 8.
All generated Test classes must be executable with the NUnit framework.
                                                                  
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
- A json property name must start with '"'.
- Do not test any exceptions.
- Do not test whether a method is throwing an exception.
- You must import System if you need it.
- Unittest files should have a specified namespace.

To make your task easier, you will generate the test files step by step:
1. Go through the list of CodeFiles and identify all classes that are relevant and eligible for testing (must be public or internal). 
Write the full class definition (access modifiers and name as one string) to a list named relevant_classes_for_testing.
2. Go through the list of relevant_classes_for_testing 
and pick the top {top_n} classes that are most relevant for testing (highest code coverage). 
Do not pick any classes that are private or abstract. Write the class names to a list named top_relevant_classes_for_testing.
3. Go through the list of top_relevant_classes_for_testing 
and for each class, extract all public and internal methods and constructors including their full definitions (method signatures and parameters). 
Write the full definitions to a list named top_relevant_classes_for_testing_with_public_methods.
4. Go through the list of top_relevant_classes_for_testing_with_public_methods
and for each class, identify the top {top_n} public methods that are most relevant for testing (highest code coverage). 
Do not pick any methods that are private or do not have any access modifier. 
Write the method names to a list named top_relevant_classes_for_testing_with_top_relevant_public_methods.
5. For each class in top_relevant_classes_for_testing_with_top_relevant_public_methods, 
define 3 potential test case names to a list named top_relevant_classes_for_testing_with_top_relevant_public_methods_with_test_case_names. 
Remember to not make any test cases that test exceptions.
6. Finally, generate one NUnit Test class (CodeFile) for each file in top_relevant_classes_for_testing_with_top_relevant_public_methods_with_test_case_names. Each CodeFile in the output json must contain:
    - A file_name property with the name of the file
    - A source_code property with the source code of the file (the source_code is encoded as a string in the json but can contain any valid C# code)
    - The source_code string must contain one test method for each test case in top_relevant_classes_for_testing_with_top_relevant_public_methods_with_test_case_names
    - The test methods must be named after the test case names
    - The test methods must be decorated with the [Test] attribute
    - The test methods must be implemented with the arrange-act-assert pattern
    - The test methods must not be empty or contain any TODOs or placeholders
    - The test methods must contain at least one assertion

The generated NUnit Test classes will be moved to a new csproj Project called TestProject.
The TestProject will reference the original project and the NUnit.Framework NuGet package.
The original project will set InternalsVisibleTo to the TestProject.
But this only makes the protected members visible to the TestProject, NOT the private members.
Therefore you must not test private methods.
Remember that in C# classes, methods and properties are private by default. Meaning that if no access modifier is specified, the member is private.
That means to test a method, it must be explicitly marked as public or protected.
Following that logic, you also cannot access private members in any of the tests.
Additionally, you are not allowed to use reflection to access private members.

When testing WPF applications, you need to run your tests in a Single Thread Apartment (STA) because WPF requires it to properly manage the threading model that handles the UI elements
Therefore, you need to add the following attribute to your at your test class after [TestFixture]: [Apartment(ApartmentState.STA)]
Remember that you have to import the System.Threading namespace to use the ApartmentState enum.


In the following you are given all filepaths and sourcecodes of a .Net project in json form.
Please generate multiple NUnit tests adhering to the above rules.
"""
)
system_message = system_message.format(
    json_output_schema=output_parser.get_format_instructions(),
    top_n=3,
)


class NUnitUTPrompter(UTPrompter):
    system_message = system_message
    examples = []
    output_parser: PydanticOutputParser = output_parser

    def convert_to_code_project(self, generation: str) -> tuple[CodeProject, bool]:
        stepbystep_output: NunitProjectStepByStepOutput = self.output_parser.parse(
            generation
        )
        logging.info(
            f"Generated NUnit files: {[f.file_name for f in stepbystep_output.nunit_files]}"
        )
        # make a codeproject from the nunit files
        parsed = CodeProject(
            files=stepbystep_output.nunit_files,
            display_name=self.source_project.display_name,
            language="csharp",
        )
        return parsed, True
