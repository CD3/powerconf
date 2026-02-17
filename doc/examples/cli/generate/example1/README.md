The `generate` command is used to interop with third-party tools that read tree-structured configuratoin data from a supported format.

Consider a fictional tool named `acme`. This tool reads configuration files in JSON format.


**acme**
```python
import sys
import json
import pathlib


config_file = pathlib.Path(sys.argv[1])

print(f"Running simulation described in {config_file}.")
config = json.loads(config_file.read_text())

print(f"Writing results to {config['simulation']['output_file']}")
pathlib.Path(config['simulation']['output_file']).write_text("done")

print("Done")

```

A typical configuration file looks something like this:

```json
import sys
import json
import pathlib


config_file = pathlib.Path(sys.argv[1])

print(f"Running simulation described in {config_file}.")
config = json.loads(config_file.read_text())

print(f"Writing results to {config['simulation']['output_file']}")
pathlib.Path(config['simulation']['output_file']).write_text("done")

print("Done")

```

and we run it like this
```bash
$ python acme ACME-solver.json

$ ls

```
We would like to powerup our `acme` config file to add unit support. We start by writing a powerconf configuration
file. We are free to structure the configuration however we want, config parameters can be given as quantities with units,
and we can use expressions that calculate the value of some parameters based on the value of others.

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

Next, we add a section to our configuration file for the acme tool. We replicate the acme config file tree
computing the value for each parameter using expressions that reference the main config.
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

# parameters that will be inserted directly into ACME config file.
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

Now we can generate an acme config file
```bash
$ powerconf generate POWERCONFIG.yml ACME-solver.json.generated -n acme -f json

$ ls
acme
ACME-simulation.json.generated
POWERCONFIG.yml

```
The `-n` option takes the name of a node. The `generate` command will write the tree below the node to the output file. The `-f` option
specifies the output file format. The generated JSON file:

```json
{
  "simulation": {
    "output_file": "acme-ouput-101.txt"
  },
  "grid": {
    "x": {
      "n": 101,
      "min": 0,
      "max": 0.009999999999999998
    },
    "y": {
      "n": 10001,
      "min": 0,
      "max": 1
    }
  }
}

```
Running `acme`:
```bash
$ python acme ACME-solver.json.generated

$ ls
acme
ACME-simulation.json.generated
POWERCONFIG.yml

```

And there you are, full-blown unit support for a tool that does not support them.
