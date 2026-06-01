Files can be included from sub-directories
  $ mkdir configs
  $ cat > main.yml << EOF
  > sim:
  >   grid:
  >     x:
  >       '@include': configs/grid.yml
  >     y:
  >       '@include': configs/grid.yml
  > EOF
  $ cat > configs/grid.yml << EOF
  > min: 0 cm
  > max: 10 cm
  > n: 100
  > EOF
  $ powerconf print-instances main.yml
  sim:
    grid:
      x:
        max: 10 centimeter
        min: 0 centimeter
        n: 100
      y:
        max: 10 centimeter
        min: 0 centimeter
        n: 100
  
@include directives in files can be included from sub-directories
are relative to the sub-directory
  $ rm * -r
Files can be included from sub-directories
  $ mkdir configs
  $ cat > configs/main.yml << EOF
  > sim:
  >   grid:
  >     x:
  >       '@include': grid.yml
  >     y:
  >       '@include': grid.yml
  > EOF
  $ cat > configs/grid.yml << EOF
  > min: 0 cm
  > max: 10 cm
  > n: 100
  > EOF
  $ powerconf print-instances configs/main.yml
  sim:
    grid:
      x:
        max: 10 centimeter
        min: 0 centimeter
        n: 100
      y:
        max: 10 centimeter
        min: 0 centimeter
        n: 100
  
@include directives in files can be included from sub-directories
are relative to the sub-directory
  $ rm * -r
