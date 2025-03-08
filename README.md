# powerconf

Powerful configuration tools for numerical simulation.

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

## Examples

See the `doc/examples` folder for examples of how to use the `powerconf` command and python module.

[`render` command example](./doc/examples/cli/render/example1/README.md)
