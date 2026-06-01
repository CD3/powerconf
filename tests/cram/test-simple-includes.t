  $ cat > main.yml << EOF
  > sim:
  >   grid:
  >     x:
  >       '@include': grid.yml
  >     y:
  >       '@include': grid.yml
  > EOF
  $ cat > grid.yml << EOF
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
  
