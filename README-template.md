# powerconf

[comment]: # {{{
[comment]: # from pathlib import *
[comment]: # }}}

Powerful configuration tools for numerical models.

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


## Using

powerconf consists of a Python module that you can use to load and/or render your configuration files and a standalone command line application.

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







## Features

