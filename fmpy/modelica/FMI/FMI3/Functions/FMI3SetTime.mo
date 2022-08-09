within FMI.FMI3.Functions;
impure function FMI3SetTime
  input Internal.ExternalFMU externalFMU;
    input Real t;
    external"C" FMU_FMI3SetTime(externalFMU, t) annotation (Library="ModelicaFMI");
end FMI3SetTime;
