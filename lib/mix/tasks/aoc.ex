defmodule Mix.Tasks.Aoc do
  use Mix.Task

  def run([]), do:  Aoc.main()

  def run(["--spoil"]), do:  Aoc.main(true)
end
