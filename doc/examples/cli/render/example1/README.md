The `render` command is used to interop with third-party tools that do not use a supported config file format.

Consider a fictional tool named `acme`. This tool reads configuration files in Pythons `configparser` format (similar to ini).


**acme**
```python
import sys
import configparser
import pathlib


config_file = pathlib.Path(sys.argv[1])

print(f"Running simulation described in {config_file}.")
config = configparser.ConfigParser()
config.read(config_file)

print(f"Writing results to {config['simulation']['output_file']}")
pathlib.Path(config['simulation']['output_file']).write_text("done")

print("Done")

```

A typical configuration file looks something like this:

```ini
[simulation]
output_file = acme-ouput.txt

[grid.x]
min = 0.0
max = 0.01
N = 101

[grid.y]
min = 0.0
max = 1
N = 10001

```

and we run it like this
```bash
$ python acme ACME-solver.ini

$ ls

```
We would like to powerup our `acme` config file to add unit suport. We start by writing a powerconf configuration
file. We are free to structure the configuration however we want, config parameters can be given as quantities with units,
and we can use expressions that calculate the value of some paraemters based on the value of others.

**POWERCONFIG.yml**
```yaml
simulation:
  grid:
    res: 1 um
    x:
      min: 0 um
      max: 100 um
      n: $(int(${max}/${../res}) + 1)
    y:
      min: 0 um
      max: 1 cm
      n: $(int(${max}/${../res}) + 1)


```

We can test that this configuration works with the `print-instances` command:

```bash
$ powerconf print-instances
simulation:
  grid:
    res: 1 micrometer
    x:
      max: 100 micrometer
      min: 0 micrometer
      n: 101
    y:
      max: 1 centimeter
      min: 0 micrometer
      n: 10001


```

Next, we add a section to our configuration file for the acme tool. We add a parameter for every value
we want to inject into our acme config, and we compute the value that will be injected using expressions.
The purpose of this section is to unit convert all parameters to the unit expected by the acme tool and
strip the units.

**POWERCONFIG.yml**
```yaml
simulation:
  grid:
    res: 1 um
    x:
      min: 0 um
      max: 100 um
      n: $(int(${max}/${../res}) + 1)
    y:
      min: 0 um
      max: 1 cm
      n: $(int(${max}/${../res}) + 1)

# parameters that will be inserted diredctly into ACME config file.
# these parameters _MUST_ be given.
# all quantities need to be converted to ACME internal units (cgs)
# and turned into plain numbers.
acme:
    simulation:
      output_file: acme-ouput-$(${../grid/x/n}).txt
    grid:
      x:
        n: $($/simulation/grid/x/n)
        min: $($/simulation/grid/x/min.to('cm').magnitude)
        max: $($/simulation/grid/x/max.to('cm').magnitude)
      y:
        n: $($/simulation/grid/y/n)
        min: $($/simulation/grid/y/min.to('cm').magnitude)
        max: $($/simulation/grid/y/max.to('cm').magnitude)

```
Nex, we write an acme configuration _template_. The template is a mustache template, `powerconf render`
will render this file using mustache with the powerconf configuration instance as a context. To inject
the parameters, we just reference the keys under the "acme" node.

**ACME-solver.ini.template**
```yaml
[simulation]
output_file = {{acme/simulation/output_file}}
[grid.x]
min = {{acme/grid/x/min}}
max = {{acme/grid/x/max}}
N = {{acme/grid/x/n}}

[grid.y]
min = {{acme/grid/y/min}}
max = {{acme/grid/y/max}}
N = {{acme/grid/y/n}}

```

And finally, we can render an ACME configuration file
```bash
$ powerconf render POWERCONFIG.yml ACME-solver.ini.template ACME-solver.ini.rendered

$ ls
ACME-solver.ini.rendered
ACME-solver.ini.template
POWERCONFIG.yml

```
The contents of `ACME-solver.ini.rendered` will be

```ini
[simulation]
output_file = {{acme/simulation/output_file}}
[grid.x]
min = {{acme/grid/x/min}}
max = {{acme/grid/x/max}}
N = {{acme/grid/x/n}}

[grid.y]
min = {{acme/grid/y/min}}
max = {{acme/grid/y/max}}
N = {{acme/grid/y/n}}

```
Running `acme`...
```bash
$ python acme ACME-solver.ini.rendered

$ ls
ACME-solver.ini.rendered
ACME-solver.ini.template
POWERCONFIG.yml

```

An there you are, full-blown unit support for a tool that does not support them.
