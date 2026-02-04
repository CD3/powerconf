# powerconf

Powerful configuration tools for numerical models.



  - [powerconf](#powerconf)
    - [Install](#install)
    - [Motivation](#motivation)
    - [Using](#using)
      - [Expression Evaluation](#expression-evaluation)
      - [Variable Expansion](#variable-expansion)
      - [Units](#units)
      - [Batch Configurations](#batch-configurations)
      - [Configuring external tools/simulations](#configuring-external-tools/simulations)
        - [`powerconf generate`](#`powerconf-generate`)
        - [`powerconf render`](#`powerconf-render`)


`powerconf` allows you to write configuration files for things like physics simulations
with support for variable interpolation and expression evaluation. Consider a simulation
that will solve some partial differential equation on a 2-dimensional Cartesian grid. Perhaps
the simulation itself requires us to set the min and max range and the number of points
to use along each axis. A simple YAML configuration for the simulation might look something
like this

```yaml
grid:
    x:
        min: 0 cm
        max: 1.5 cm
        N: 151
    y:
        min: 0 cm
        max: 1.0 cm
        N: 101
```
This is fine, but it might be useful to specify the resolution to use instead of the number of points.
With `powerconf`, we can write a configuration file that looks like this

```yaml
grid:
    resolution: 1 um
    x:
        min: 0 cm
        max: 1.5 cm
        N: $( (${max} - ${min})/${../resolution} + 1)
    y:
        min: 0 cm
        max: 1.0 cm
        N: $( (${max} - ${min})/${../resolution} + 1)
```
In this example, we give a resolution to use for both x and y directions and then calculate the number
of points to use with an expression. Note the relative paths to configuration parameters used in the
expressions. `powerconf` uses the [`fspathtree`](https://github.com/CD3/fspathtree) module to provide
filesystem-like access to elements in a nested dict.


## Install

Install with pip

```bash
$ pip install powerconf
```

or `pipx`

```bash
$ pipx install powerconf
```

or, my favorite, `uv`

```bash
$ uv tool install powerconf
```


## Motivation

Let's say you are writing a model in Python to do some sort of physics calculation. 
The model will discretize some continuous variable along the x-axis to some finite grid.
The model takes the minimum and maximum values of x and the number of grid points to use as configuration
input and performs the discretization accordingly. The configuration file might look like this:

```yaml
grid:
    x:
        min: 0
        max: 2
        n: 200
```


Now perhaps you want to allow the user to specify a grid resolution instead of the number of points (since
the resolution will impact the model convergence). You can easily add support for this to your model. You simply check
to see if a resolution parameter is present, and if so, compute the number of grid points. If not, use the number of grid points.
That will not be too difficult. The configuration file might look like this:

```yaml
grid:
    x:
        min: 0
        max: 2
        resolution: 0.01
```

But what if your model is 3-D? Then you need to add this check-and-calculate in three different places. What if you wanted to
allow the user to give a minimum x value and a thickness? Or a maximum x value and a thickness? A configuration file could look
like this:

```yaml
grid:
    x:
        min: 0
        max: 2
        n: 0.01
    y:
        min: 1
        thickness: 4
        resolution: 0.01
    z:
        max: 1
        thickness: 2
        resolution: 0.02
```

There are all sorts of different
combinations of configuration parameters that might be more convenient for the user.

With powerconf, you move this complexity out of the model and into the configuration file. Admittedly, the burden
is shifted to the user, but the tradeoff is that they can use any configuration parameters that they want, as long as they
know how to compute the parameters your model needs. And, if you are the main user of your model, then the ability
to quickly configure the model with new configuration parameters without having to modify code is huge.


## Using

powerconf consists of a Python module that you can use to load and/or render your configuration files and a standalone command line application.

### Expression Evaluation

Values of configuration parameters can contain Python expressions that will be evaluated to produce the parameter value. Expressions are identified with a `$(...)` (similar to common shells).



```bash
$cat CONFIG.yaml
grid:        
 theta:      
   min: 0    
   max: $(2*math.pi)
$ powerconf print-instances CONFIG.yaml
grid:
  theta:
    max: 6.283185307179586
    min: 0


```

An expression can be embedded in surrounding text



```bash
$cat CONFIG.yaml
grid:        
 theta:      
   min: 0    
   max: $(2*math.pi)  
outfile: output-$(2*math.pi).txt
$ powerconf print-instances CONFIG.yaml
grid:
  theta:
    max: 6.283185307179586
    min: 0
outfile: output-6.283185307179586.txt


```

A parameter value can also contain multiple expressions



```bash
$cat CONFIG.yaml
grid:        
 theta:      
   min: $(math.pi)    
   max: $(2*math.pi)  
outfile: output-$(math.pi)_to_$(2*math.pi).txt
$ powerconf print-instances CONFIG.yaml
grid:
  theta:
    max: 6.283185307179586
    min: 3.141592653589793
outfile: output-3.141592653589793_to_6.283185307179586.txt


```

### Variable Expansion

The real power of PowerConf is its ability to reference the value of other
parameters inside an expression. Parameter values are identified with a `${...}`
(again, similar to common shells).



```bash
$cat CONFIG.yaml
grid:        
 x:      
   min: 0    
   max: 4  
   N: $( (${max} - ${min})/0.1 )
$ powerconf print-instances CONFIG.yaml
grid:
  x:
    N: 40.0
    max: 4
    min: 0


```

Here, the parameter `N` is computed from the values of `min` and `max`. We could
even use an intermdiate parameter to specify the resolution.




```bash
$cat CONFIG.yaml
grid:        
 x:      
   res: 0.1    
   min: 0    
   max: 4  
   N: $( (${max} - ${min})/${res} )
$ powerconf print-instances CONFIG.yaml
grid:
  x:
    N: 40.0
    max: 4
    min: 0
    res: 0.1


```

Expressions can reference parameters who's values also contain expressions.


```bash
$cat CONFIG.yaml
node1:        
 node2:      
   val1: 0.1    
   val2: $(${val1})    
   val3: $(${val2})
$ powerconf print-instances CONFIG.yaml
node1:
  node2:
    val1: 0.1
    val2: 0.1
    val3: 0.1


```


PowerConf will determine the correct order to evaluate the expressions in. It will
also detect circular dependencies and throw an error if it detects one.


```bash
$cat CONFIG.yaml
node1:        
 node2:      
   val1: $(${val3})    
   val2: $(${val1})    
   val3: $(${val2})
$ powerconf print-instances CONFIG.yaml
╭───────────────────── Traceback (most recent call last) ──────────────────────╮
│ /home/cclark/Code/sync/projects/powerconf/src/powerconf/cli.py:185 in        │
│ print_instances                                                              │
│                                                                              │
│   182 │   """                                                                │
│   183 │   Print instances of configuration trees generated from the config.  │
│   184 │   """                                                                │
│ ❱ 185 │   configs = yaml.powerload(config_file, njobs=njobs)                 │
│   186 │   configs = utils.apply_transform(                                   │
│   187 │   │   configs, lambda p, n: str(n), lambda p, n: hasattr(n, "magnitu │
│   188 │   )                                                                  │
│                                                                              │
│ ╭────────────────── locals ───────────────────╮                              │
│ │ config_file = PosixPath('/tmp/tmpimf1mmgb') │                              │
│ │       njobs = 1                             │                              │
│ ╰─────────────────────────────────────────────╯                              │
│                                                                              │
│ /home/cclark/Code/sync/projects/powerconf/src/powerconf/yaml.py:96 in        │
│ powerload                                                                    │
│                                                                              │
│    93 │   │   │   │   *list(map(config_renderer.expand_batch_nodes, complete │
│    94 │   │   │   )                                                          │
│    95 │   │   )                                                              │
│ ❱  96 │   │   rendered_configs = list(map(config_renderer.render, unrendered │
│    97 │   │   if transform is not None:                                      │
│    98 │   │   │   utils.apply_transform(rendered_configs, transform)         │
│    99 │   │   return rendered_configs                                        │
│                                                                              │
│ ╭───────────────────────────────── locals ─────────────────────────────────╮ │
│ │   complete_configs = [                                                   │ │
│ │                      │   <fspathtree.fspathtree.fspathtree object at     │ │
│ │                      0x76b860b48200>                                     │ │
│ │                      ]                                                   │ │
│ │        config_docs = [                                                   │ │
│ │                      │   <fspathtree.fspathtree.fspathtree object at     │ │
│ │                      0x76b860b48200>                                     │ │
│ │                      ]                                                   │ │
│ │        config_file = PosixPath('/tmp/tmpimf1mmgb')                       │ │
│ │    config_renderer = <powerconf.rendering.ConfigRenderer object at       │ │
│ │                      0x76b860994e90>                                     │ │
│ │              njobs = 1                                                   │ │
│ │          transform = None                                                │ │
│ │ unrendered_configs = [                                                   │ │
│ │                      │   <fspathtree.fspathtree.fspathtree object at     │ │
│ │                      0x76b860916660>                                     │ │
│ │                      ]                                                   │ │
│ ╰──────────────────────────────────────────────────────────────────────────╯ │
│                                                                              │
│ /home/cclark/Code/sync/projects/powerconf/src/powerconf/rendering.py:211 in  │
│ render                                                                       │
│                                                                              │
│   208 │   │   │   msg = "Circular dependencies detected."                    │
│   209 │   │   │   for cycle in cycles:                                       │
│   210 │   │   │   │   msg += "(" + " -> ".join(map(str, cycle)) + ")"        │
│ ❱ 211 │   │   │   raise RuntimeError(msg)                                    │
│   212 │   │                                                                  │
│   213 │   │   # make a copy to work with                                     │
│   214                                                                        │
│                                                                              │
│ ╭───────────────────────────────── locals ─────────────────────────────────╮ │
│ │    config = <fspathtree.fspathtree.fspathtree object at 0x76b860916660>  │ │
│ │     cycle = [                                                            │ │
│ │             │   PurePosixPath('/node1/node2/val3'),                      │ │
│ │             │   PurePosixPath('/node1/node2/val2'),                      │ │
│ │             │   PurePosixPath('/node1/node2/val1')                       │ │
│ │             ]                                                            │ │
│ │    cycles = [                                                            │ │
│ │             │   [                                                        │ │
│ │             │   │   PurePosixPath('/node1/node2/val3'),                  │ │
│ │             │   │   PurePosixPath('/node1/node2/val2'),                  │ │
│ │             │   │   PurePosixPath('/node1/node2/val1')                   │ │
│ │             │   ]                                                        │ │
│ │             ]                                                            │ │
│ │       dep = PurePosixPath('/node1/node2/val2')                           │ │
│ │         G = <networkx.classes.digraph.DiGraph object at 0x76b860a17770>  │ │
│ │ make_copy = True                                                         │ │
│ │       msg = 'Circular dependencies detected.(/node1/node2/val3 ->        │ │
│ │             /node1/node2/val2 -> /node1'+12                              │ │
│ │      node = PurePosixPath('/node1/node2/val3')                           │ │
│ │      self = <powerconf.rendering.ConfigRenderer object at                │ │
│ │             0x76b860994e90>                                              │ │
│ │         v = PurePosixPath('val2')                                        │ │
│ │ variables = [PurePosixPath('val2')]                                      │ │
│ ╰──────────────────────────────────────────────────────────────────────────╯ │
╰──────────────────────────────────────────────────────────────────────────────╯
RuntimeError: Circular dependencies detected.(/node1/node2/val3 -> 
/node1/node2/val2 -> /node1/node2/val1)

```

PowerConf uses the [fspathtree](https://github.com/cd3/fspathtree) library for storing the configuration tree,
so you can use relative or absolute paths to access any parameter in the tree.

```bash
$cat CONFIG.yaml
grid:        
 res: 0.1 
 x:      
   min: -1    
   max: 1    
   N: $( int( (${max}-${min})/${../res} ) )   
 y:      
   min: $(${../x/min})    
   max: $(${../x/max})    
   N: $(${../x/N})   
 z:      
   min: 0   
   max: 5    
   N: $( int( (${max}-${min})/${../res} ) )   
output:           
  dir: full_sim-res-$(${/grid/res})
$ powerconf print-instances CONFIG.yaml
grid:
  res: 0.1
  x:
    N: 20
    max: 1
    min: -1
  y:
    N: 20
    max: 1
    min: -1
  z:
    N: 50
    max: 5
    min: 0
output:
  dir: full_sim-res-0.1


```

### Units

PowerConf supports units. Any parameter can be given as a quantity (a value with a unit).
This turns out to be _really_ useful, especially when configuring physics simulation.
PowerConf will try to convert any string to a quantity, so defining parameters as quantities is natural.

```bash
$cat CONFIG.yaml
grid:        
 res: 10 um 
 x:      
   min: -1 cm   
   max: 1 cm   
   N: $( int( (${max}-${min})/${../res} ) )
$ powerconf print-instances CONFIG.yaml
grid:
  res: 10 micrometer
  x:
    N: 2000
    max: 1 centimeter
    min: -1 centimeter


```

PowerConf uses [pint](https://pint.readthedocs.io/en/stable/) to handle quantities, so any unit
handled by pint is supported by PowerConf (which is a lot). For me, this is one of _the_ most useful features
of PowerConf. Instead of giving a physical parameter (say thermal conductivity) as a numerical value in the units
that the simulation you are configuring uses, you give it as a quantity in whatever unit the source you looked
up the quantity uses.

### Batch Configurations

PowerConf also supports generating multiple configurations. This is useful when running simulations to see investigate a trend (i.e.
laser damage threshold as a function of wavelength). There are two ways to generate multiple configurations. The first is by
using the '@batch' keyword.

```bash
$cat CONFIG.yaml
grid:        
 res: 
   '@batch': 
     - 1 um 
     - 10 um 
     - 100 um 
 x:      
   min: -1 cm   
   max: 1 cm   
   N: $( int( (${max}-${min})/${../res} ) )
$ powerconf print-instances CONFIG.yaml
grid:
  res: 1 micrometer
  x:
    N: 20000
    max: 1 centimeter
    min: -1 centimeter

---
grid:
  res: 10 micrometer
  x:
    N: 2000
    max: 1 centimeter
    min: -1 centimeter

---
grid:
  res: 100 micrometer
  x:
    N: 200
    max: 1 centimeter
    min: -1 centimeter


```

*Note that @batch needs to be quoted here so that the yaml parser will treat it as a string*.
Any parameter can be given multiple values by repacing its value with a '@batch` node. When PowerConf
sees a '@batch' node, it creates multiple copies of the configuration tree, one for each value in the '@batch' node.

Multiple parameters can be batched.

```bash
$cat CONFIG.yaml
laser:        
 wavelength: 
   '@batch': 
     - 500 nm 
     - 600 nm 
     - 700 nm 
 one_over_e_diameter: 
   '@batch':           
     - 1 mm           
     - 3 mm           
     - 1 cm
$ powerconf print-instances CONFIG.yaml
laser:
  one_over_e_diameter: 1 millimeter
  wavelength: 500 nanometer

---
laser:
  one_over_e_diameter: 3 millimeter
  wavelength: 500 nanometer

---
laser:
  one_over_e_diameter: 1 centimeter
  wavelength: 500 nanometer

---
laser:
  one_over_e_diameter: 1 millimeter
  wavelength: 600 nanometer

---
laser:
  one_over_e_diameter: 3 millimeter
  wavelength: 600 nanometer

---
laser:
  one_over_e_diameter: 1 centimeter
  wavelength: 600 nanometer

---
laser:
  one_over_e_diameter: 1 millimeter
  wavelength: 700 nanometer

---
laser:
  one_over_e_diameter: 3 millimeter
  wavelength: 700 nanometer

---
laser:
  one_over_e_diameter: 1 centimeter
  wavelength: 700 nanometer


```

When multiple parameters are batched, a configuration for every combination of parameters is generated.

The second way to generate multiple parameters is to use multiple yaml documents.

```bash
$cat CONFIG.yaml
grid:    
 x:      
   min: -1 cm   
   max: 1 cm   
   N: $( int( (${max}-${min})/${../res} ) )   
--- 
grid:        
 res: 1 um  
--- 
grid:        
 res: 10 um  
--- 
grid:        
 res: 100 um
$ powerconf print-instances CONFIG.yaml
grid:
  res: 1 micrometer
  x:
    N: 20000
    max: 1 centimeter
    min: -1 centimeter

---
grid:
  res: 10 micrometer
  x:
    N: 2000
    max: 1 centimeter
    min: -1 centimeter

---
grid:
  res: 100 micrometer
  x:
    N: 200
    max: 1 centimeter
    min: -1 centimeter


```

When PowerConf sees multiple documents, it treats the first document is a
"baseline" configuration and each document
that follows as a modification of the baseline.

The two batch methods are not separate, they can be used together, and sometimes
this is useful when you want to batch to parameters but you don't
want all possible combinations.

```
```bash
$cat CONFIG.yaml
laser:    
 wavelength: 532 nm     
--- 
laser:    
 exposure_duration: 10 us     
 one_over_e_diameter:     
   '@batch':              
     - 20 um              
     - 40 um              
--- 
laser:    
 exposure_duration: 100 us     
 one_over_e_diameter:     
   '@batch':              
     - 100 um              
     - 200 um
$ powerconf print-instances CONFIG.yaml
laser:
  exposure_duration: 10 microsecond
  one_over_e_diameter: 20 micrometer
  wavelength: 532 nanometer

---
laser:
  exposure_duration: 10 microsecond
  one_over_e_diameter: 40 micrometer
  wavelength: 532 nanometer

---
laser:
  exposure_duration: 100 microsecond
  one_over_e_diameter: 100 micrometer
  wavelength: 532 nanometer

---
laser:
  exposure_duration: 100 microsecond
  one_over_e_diameter: 200 micrometer
  wavelength: 532 nanometer


```
```

### Configuring external tools/simulations

#### `powerconf generate`

If your writing a new model in Python, you can use PowerConf to load your
configuration from yaml files.

```python
import pathlib
from powerconf import yaml

configs = yaml.powerload(pathlib.Path("CONFIG.yml"))

for config in configs:
    xmin = config["/grid/x/min"])
    xmax = config["/grid/x/max"])
    ...
```


If you are using a legacy model or a model
that you didn't write, you will have to configure the model using a file format
supported by the model. If the model reads yaml or json, you can use `powerconf generate` to write configuration file(s)

```bash
$cat CONFIG.yaml
grid:        
 res: 0.1 
 x:      
   min: -1    
   max: 1    
   N: $( int( (${max}-${min})/${../res} ) )
$ powerconf generate CONFIG.yaml CONFIG2.yaml
$ cat CONFIG2.yaml
grid:
  res: 0.1
  x:
    N: 20
    max: 1
    min: -1

$ powerconf generate --format json CONFIG.yaml CONFIG2.json
$ cat CONFIG2.json
{"grid": {"res": 0.1, "x": {"min": -1, "max": 1, "N": 20}}}
```

It is often more convenient to add a separate node in your configuration just for the model your configuring. This is useful for
adding support for legacy models or even configuration multiple models with a shared configuration.


```bash
$cat CONFIG.yaml
grid:        
 res: 10 um 
 x:      
   min: -1 cm   
   max: 1 cm   
   N: $( int( (${max}-${min})/${../res} ) )   
acme:  
 grid: 
   x:  
     min: $(${/grid/x/min}.to('mm').magnitude) 
     max: $(${/grid/x/max}.to('mm').magnitude) 
     N: $(int(${/grid/x/N})) 
wile-e:  
  x_min: $(${/grid/x/min}.to('cm').magnitude) 
  x_max: $(${/grid/x/max}.to('cm').magnitude) 
  x_N: $(int(${/grid/x/N}))
$ powerconf generate CONFIG.yaml ACME-CONFIG.yaml --node acme
$ cat ACME-CONFIG.yaml
grid:
  x:
    N: 2000
    max: 10.0
    min: -10.0

$ powerconf generate CONFIG.yaml ACME-CONFIG.yaml --node wile-e
$ cat WILE-E-CONFIG.yaml
x_N: 2000
x_max: 1
x_min: -1

```

Here we are configuring two fictional models named `acme` and `wile-e`. The models both have grid configurations, but they use
different names and expect their input as plain numbers expressed in different units.
The `--node`  option tells PowerConf to extract the tree under the specified node and write it as the root of the output configuration.

`poerconf generate` can also handle batch configurations, in which case it will write the configuration files to a subdirectory.


```bash
$cat CONFIG.yaml
grid:        
 res:
   '@batch':
     - 10 um
     - 20 um
 x:      
   min: -1 cm   
   max: 1 cm   
   N: $( int( (${max}-${min})/${../res} ) )   
acme:  
 grid: 
   x:  
     min: $(${/grid/x/min}.to('mm').magnitude) 
     max: $(${/grid/x/max}.to('mm').magnitude) 
     N: $(int(${/grid/x/N})) 
wile-e:  
  x_min: $(${/grid/x/min}.to('cm').magnitude) 
  x_max: $(${/grid/x/max}.to('cm').magnitude) 
  x_N: $(int(${/grid/x/N}))
$ powerconf generate CONFIG.yaml ACME-CONFIG.d --node acme
$ ls
ACME-CONFIG.d
CONFIG.yaml

$ ls ACME-CONFIG.d
ACME-CONFIG-20fd79d04b155c6aea97cb159d85657b.d
ACME-CONFIG-9cc6e43c610684d5e7348fcc34d71767.d

```


#### `powerconf render`

For models that read some other configuration file format (which is probably
more common), the `powerconf render` command can be used to generate
configuration file instances from a template.  This requires an additional
template file to be supplied.


```bash
$cat CONFIG.yaml
grid:        
 res: 10 um 
 x:      
   min: -1 cm   
   max: 1 cm   
   N: $( int( (${max}-${min})/${../res} ) )   
acme:  
 grid: 
   x:  
     min: $(${/grid/x/min}.to('mm').magnitude) 
     max: $(${/grid/x/max}.to('mm').magnitude) 
     N: $(int(${/grid/x/N}))
$cat ACME-CONFIG.txt.template
# out grid configuration                
grid.x.min = {{acme/grid/x/min}}        
grid.x.max = {{acme/grid/x/min}}        
grid.x.N   = {{acme/grid/x/N}}        
# our material configuration          
material.density = 1                  
material.specific_heat = 4.18               
material.thermal_conductivity = 0.004
$ powerconf render CONFIG.yaml ACME-CONFIG.txt.template ACME-CONFIG.txt
$ ls
ACME-CONFIG.txt
ACME-CONFIG.txt.template
CONFIG.yaml

$ cat ACME-CONFIG.txt
# out grid configuration                
grid.x.min = -10.0        
grid.x.max = -10.0        
grid.x.N   = 2000        
# our material configuration          
material.density = 1                  
material.specific_heat = 4.18               
material.thermal_conductivity = 0.004
```

The template configuration file is a [mustache](https://mustache.github.io/) template that is rendered with the configuration
tree instance as a context. Note that there is **no** leading `/` in the mustache template syntax.

`powerconf render` can handle batch configurations too. Configuration files written to a subdirectory just as with `powerconf generate`.

