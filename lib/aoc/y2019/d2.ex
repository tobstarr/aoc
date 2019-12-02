defmodule  Aoc.Y2019.D2 do
  use  Aoc.Boilerplate,
      transform: fn raw ->
        raw
        |> String.split(",")
        |> Enum.map(&String.to_integer(&1))
      end
      
  def part1(input \\ processed()) do
    lookup_table(input)
    |> Map.merge(%{1 => 12, 2 => 2})
    |> process()
  end
  
  def part2(input \\ processed()) do
    lookup = lookup_table(input)

    result =
      for noun <- 0..99,
          verb <- 0..99, into: %{} do
      
        processed =
          lookup
          |> Map.merge(%{1 => noun, 2 => verb})
          |> process()
      
        {processed, {noun, verb}}
      end
    
    {noun, verb} = result[19690720]
    100 * noun + verb
  end
  
  defp lookup_table(list) do
    0..length(list) - 1
    |> Stream.zip(list)
    |> Enum.into(%{})
  end
  
  defp process(lookup, position \\ 0) do
    case lookup[position] do
      99 ->
        lookup[0]
      opcode ->
        lookup
        |> run_operation(opcode, lookup[position + 1], lookup[position + 2], lookup[position + 3])
        |> process(position + 4)
    end
  end
  
  defp run_operation(lookup, 1, x_position, y_position, z_position) do
    lookup
    |> Map.put(z_position, lookup[x_position] + lookup[y_position])
  end
  
  defp run_operation(lookup, 2, x_position, y_position, z_position) do
    lookup
    |> Map.put(z_position, lookup[x_position] * lookup[y_position])
  end
end