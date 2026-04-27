---
name: spring-boot
category: frameworks
description: Spring Boot startup failures, bean wiring, actuator and classloader issues
applicable_when:
  - framework_is: "spring-boot"
  - framework_is: "spring"
  - tech_stack_includes: "spring"
  - error_contains: "BeanCreationException"
  - error_contains: "BeanInstantiationException"
  - error_contains: "NoSuchBeanDefinitionException"
  - error_contains: "CircularReferenceException"
  - error_contains: "UnsatisfiedDependencyException"
  - error_contains: "ApplicationContextException"
severity_hint: medium
---

# Spring Boot investigation cheatsheet

## Where to look first
- **Startup log, top to bottom.** Spring dumps the failing bean and
  its dependency chain as the first thing. Scroll to the FIRST
  `Error creating bean with name '...'` — later ones are downstream
  damage.
- **Auto-configuration report.** Start with
  `-Ddebug=true` or `DEBUG=true` env var and the AutoConfigReport
  at the end of the log shows which `@Configuration`s matched and
  which were excluded, and why.
- **Actuator `/actuator/conditions`** — same data, live, on a
  running app.

## Common failure shapes
- **`NoSuchBeanDefinitionException: No qualifying bean of type X`.**
  The `@Service` / `@Component` wasn't scanned. Is its package
  under `@SpringBootApplication`'s default scan root? Add
  `@ComponentScan(basePackages=...)` or move the class.
- **`UnsatisfiedDependencyException` → Circular reference.** Two
  beans depend on each other. Introduce an interface, inject via
  setter rather than constructor, or break the cycle with an
  `@Lazy` qualifier.
- **`BeanCreationException` caused by `DataSource` setup.** Missing
  `spring.datasource.url` / wrong JDBC driver on the classpath /
  test profile pulling in H2 instead of Postgres. Check
  `application-<profile>.yml`.
- **`ApplicationContextException: Unable to start ServletWebServerApplicationContext`.**
  Usually port already in use or SSL keystore missing. The
  second-last log line usually names the port.
- **Slow startup.** JPA / Hibernate scanning thousands of entities,
  or auto-configured but unused modules. Add `spring.main.lazy-initialization=true`
  for dev; in prod, narrow `@EntityScan`.

## Useful commands
- `./mvnw spring-boot:run -Ddebug=true` or `./gradlew bootRun --debug`.
- `curl :8080/actuator/health /actuator/info /actuator/conditions` —
  only enabled in prod if you've whitelisted them in
  `management.endpoints.web.exposure.include`.
- `jstack <pid>` on a hung boot process — often waiting on a socket
  or a blocked `@PostConstruct`.
