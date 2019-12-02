defmodule  Aoc.Boilerplate do
  defstruct [:raw, :file, :transform, :part1, :part2]

  defmacro __using__(opts), do: using(opts, __CALLER__)

  defp using(list_of_opts, opts \\ %__MODULE__{}, caller)
  defp using([{:raw, raw} | t], opts, caller), do: using(t, %{opts | raw: raw}, caller)
  defp using([{:file, file} | t], opts, caller), do: using(t, %{opts | file: file}, caller)
  defp using([{:part1, part1} | t], opts, caller), do: using(t, %{opts | part1: part1}, caller)
  defp using([{:part2, part2} | t], opts, caller), do: using(t, %{opts | part2: part2}, caller)

  defp using([{:transform, transform} | t], opts, caller),
    do: using(t, %{opts | transform: transform}, caller)

  defp using([], opts, caller) do
    file =
      opts.file ||
        :code.priv_dir(:aoc)
        |> Path.join(
          caller.file
          |> String.replace_suffix(".ex", ".txt")
          |> Path.relative_to(Path.join(File.cwd!(), "lib"))
        )

    raw = opts.raw || File.read!(file)

    part1 = opts.part1 || quote do: &part1/0
    part2 = opts.part2 || quote do: &part2/0

    transformer =
      opts.transform ||
        quote do
          fn a -> a end
        end

    quote do
      @external_resource unquote(file)
      @__processed__ unquote(raw) |> String.trim() |> unquote(transformer).()

      def processed(), do: @__processed__

      def main(spoil \\ false) do
        [part1: unquote(part1), part2: unquote(part2)]
        |> Enum.each(fn {n, f} ->
          {t, v} = :timer.tc(f)
          IO.puts("#{unquote(caller.module)}, #{n} => #{t / 1_000}ms; <#{:erlang.phash2(v)}>")
          if spoil, do: IO.puts("#{unquote(caller.module)}, #{n} -> #{v}")
        end)
      end
    end
  end
end
