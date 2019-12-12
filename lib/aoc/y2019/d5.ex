defmodule Aoc.Y2019.D5 do
  use Aoc.Boilerplate,
    transform: fn raw ->
      raw
      |> String.split(",")
      |> Enum.map(&String.to_integer(&1))
    end

  def part1(input \\ processed()) do
    lookup_table(input)
  end

  def part2(input \\ processed()) do
    lookup = lookup_table(input)
  end

  defp lookup_table(list) do
    0..(length(list) - 1)
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

  def instructions(opcode) do
    instruction =
      case rem(opcode, 100) do
        1 -> :add
        2 -> :multiply
      end

    param_1_mode = if rem(div(opcode, 100), 10) == 1, do: :immediate, else: :position
    param_2_mode = if rem(div(opcode, 1000), 10) == 1, do: :immediate, else: :position
    param_3_mode = if rem(div(opcode, 10000), 10) == 1, do: :immediate, else: :position
    {instruction, param_1_mode, param_2_mode, param_3_mode}
  end
end
