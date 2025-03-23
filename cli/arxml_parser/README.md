
## Element-Query Syntax
### `:Path`
*Definition*: Full path of an element (e.g., nested AR-Package(s), and short name).
* The wildcard character, `*`, is supported.
* If a wildcard character is used (i.e., `*`), search is case-insentive.
* Otherwise, search is case-sensitive and an exact match is a MUST.
### `:Type`
*Definition*: Type of element (e.g., `ETHERNET-CLUSTER`).
* The wildcard character, `*`, is supported.
* If no wildcard character is used, an exact match is a MUST.
* Search is always case-insensitive.
### `:Contains`
*Definition*: Text that the element contains.
* If field is unspecified, it is ignored.
* Search occurs based on the render-mode (i.e., `XML` or model-based).
* The wildcard character, `*`, is supported.
* Search case-sensitivity is configurable.