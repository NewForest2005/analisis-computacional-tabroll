#!/usr/bin/perl

# This script takes a "chord-list" as input (see www.theory.esm.rochester.edu/temperley/kp-stats for explanation)
# and outputs aggregate harmonic statistics. Give the input file as standard input, e.g. "cat [input-file] | ./tally.pl"

# START END ROMNUM CROOT DROOT KEY AROOT
# 0     1   2      3     4     5   6 


for($c=0; $c<12; $c++) {
    $chord_count[$c] = 0;
    $chord_time[$c] = 0;
    for($c2=0; $c2<12; $c2++) {
	$trans[$c][$c2] = 0;
    }
}

$misc_count = $misc_time = 0;

while(<STDIN>) {   
    $line = $_;
    chomp($line);
    $line =~ s/^[ ]+//;
    @words = split(/[ ]+/, $line);

    if($words[0] eq "%") {
	# printf("%s\n", $words[1]);
	next;
    }

    if($words[0] eq "---") {
	$c=0;
    }

    else {
	if($words[3] != -1) {
	    $chord_count[$words[3]]++;
	    $chord_time[$words[3]] += $words[1] - $words[0];
	}
	else {
	    $misc_count++;
	    $misc_time += $words[1] - $words[0];
	}
	if($c!= 0 && $words[3] != -1 && $prev_croot != -1) {
	    if($words[5] == $prev_key) {
		$trans[$prev_croot][$words[3]]++;
		#printf("Adding for %d %d\n", $prev_croot, $words[3]);
	    }
	}
	$prev_croot = $words[3];
	$prev_key = $words[5];
	$c++;
    }
}

$total_count = $total_time = $total_nontonic_count = 0;
for($c=0; $c<12; $c++) {
    $total_count += $chord_count[$c];
    if($c != 0) {
	$total_nontonic_count += $chord_count[$c];	
    }
    $total_time += $chord_time[$c];
}
$total_count += $misc_count;
$total_time += $misc_time;

printf("\nTotal chord count = %d; total time = %.3f\n\n", $total_count, $total_time);

printf("Counts and time for chromatic roots (0=I, 1=bII, etc.)\n");
printf("[Root: count (proportion; proportion excluding tonic), time (proportion)]\n");
for($c=0; $c<12; $c++) {
    if($c==0) {
	printf("%d: %d (%5.3f; ---), %6.3f (%5.3f)\n", $c, $chord_count[$c], $chord_count[$c]/$total_count, $chord_time[$c], $chord_time[$c]/$total_time);
    }
    else {
	printf("%d: %d (%5.3f; %5.3f), %6.3f (%5.3f)\n", $c, $chord_count[$c], $chord_count[$c]/$total_count, $chord_count[$c]/$total_nontonic_count, $chord_time[$c], $chord_time[$c]/$total_time);
    }
}
printf("\n");

printf("%d misc chords, time = %.3f\n\n", $misc_count, $misc_time);

for($c=0; $c<12; $c++) {
    $cons_total[$c] = $ant_total[$c] = 0;
}

for($c=0; $c<12; $c++) {
    for($c2=0; $c2<12; $c2++) {
	$cons_total[$c] += $trans[$c2][$c];
	$ant_total[$c2] += $trans[$c2][$c];
    }
}

printf("Chromatic root transition counts\n");
printf(" Cons");
for($c2=0; $c2<12; $c2++) {
    printf("%4d ", $c2);
}
printf("\nAnt \n");
for($c=0; $c<12; $c++) {
    printf("%4d ", $c);
    for($c2=0; $c2<12; $c2++) {
	printf("%4d ", $trans[$c][$c2]);
    }
    printf("\n");
}

printf("\nChromatic root transitions as proportion of count for CONSEQUENT chord\n");
printf(" Cons");
for($c2=0; $c2<12; $c2++) {
    printf("%6d", $c2);
}
printf("\nAnt \n");
for($c=0; $c<12; $c++) {
    printf("%4d  ", $c);
    for($c2=0; $c2<12; $c2++) {
	if($cons_total[$c2] > 0) {
	    printf("%.3f ", $trans[$c][$c2] / $cons_total[$c2]);
	}
	else {
	    printf("0.000 ");
	}
    }
    printf("\n");
}

printf("\nChromatic root transitions as proportion of count for ANTECEDENT chord\n");
printf(" Cons");
for($c2=0; $c2<12; $c2++) {
    printf("%6d", $c2);
}
printf("\nAnt \n");
for($c=0; $c<12; $c++) {
    printf("%4d  ", $c);
    for($c2=0; $c2<12; $c2++) {
	if($ant_total[$c] > 0) {
	    printf("%.3f ", $trans[$c][$c2] / $ant_total[$c]);
	}
	else {
	    printf("0.000 ");
	}
    }
    printf("\n");
}

for($i=0; $i<12; $i++) {
    $dia[$i] = 0;
    $chro[$i] = 0;
}

for($c=0; $c<12; $c++) {
    for($c2=0; $c2<12; $c2++) {
	$i = (($c2+12) - $c) % 12;
	$chro[$i] += $trans[$c][$c2];
	if($i == 0) {
	    $dia[0] += $trans[$c][$c2];
	}
	elsif($i < 3) {
	    $dia[1] += $trans[$c][$c2];
	}
	elsif($i < 5) {
	    $dia[2] += $trans[$c][$c2];
	}
	elsif($i < 6) {
	    $dia[3] += $trans[$c][$c2];
	}
	elsif($i < 7) {
	    $dia[7] += $trans[$c][$c2];        # Special case: dia[7] = tritone!
	}
	elsif($i < 8) {
	    $dia[4] += $trans[$c][$c2];
	}
	elsif($i < 10) {
	    $dia[5] += $trans[$c][$c2];
	}
	else {
	    $dia[6] += $trans[$c][$c2];
	}
    }
}

printf("\nChromatic interval counts:\n");
for($i=0; $i<12; $i++) {
    printf("%d: %d\n", $i, $chro[$i]);
}

printf("Diatonic interval counts:\n");
printf("+M/m2: %d\n", $dia[1]);
printf("-M/m2: %d\n", $dia[6]);
printf("+M/m3: %d\n", $dia[2]);
printf("-M/m3: %d\n", $dia[5]);
printf("+P4/-P5: %d\n", $dia[3]);
printf("-P4/+P5: %d\n", $dia[4]);
printf("TT: %d\n", $dia[7]);

	

