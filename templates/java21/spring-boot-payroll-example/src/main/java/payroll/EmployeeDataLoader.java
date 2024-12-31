package payroll;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.io.ResourceLoader;
import org.springframework.stereotype.Service;
import jakarta.annotation.PostConstruct;
import java.io.IOException;
import java.io.InputStream;
import java.util.List;
import java.util.Map;

@Service
public class EmployeeDataLoader {

    @Autowired
    private EmployeeRepository repository;

    @Autowired
    private ResourceLoader resourceLoader;

    @PostConstruct
    public void loadEmployeeData() throws IOException {
        ObjectMapper mapper = new ObjectMapper(new YAMLFactory());
        InputStream inputStream = resourceLoader.getResource("classpath:initial_employees.yaml").getInputStream();
        Map<String, List<Map<String, String>>> data = mapper.readValue(inputStream, Map.class);
        List<Map<String, String>> employees = data.get("employees");
        employees.forEach(empMap -> {
            Employee employee = new Employee(empMap.get("name"), empMap.get("role"));
            repository.save(employee);
        });
    }
}
