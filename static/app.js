new Vue({
    el: '#app',
    data: {
        slots: [],
        cheapestCount: 10,
        title: '',
        showApiDetails: false
    },
    methods: {
        async fetchAllSlots() {
            try {
                const response = await axios.get('/api/all_slots');
                this.slots = this.groupAndColorSlots(response.data);
                this.title = 'All upcoming slots';
            } catch (error) {
                console.error('Error fetching all slots:', error);
            }
        },
        async fetchCheapestSlots() {
            try {
                const response = await axios.get(`/api/cheapest_slots/${this.cheapestCount}`);
                this.slots = this.groupAndColorSlots(response.data);
                this.title = `${this.cheapestCount} cheapest upcoming slots`;
            } catch (error) {
                console.error('Error fetching cheapest slots:', error);
            }
        },
        async fetchCheapestSlotsTomorrow() {
            try {
                const response = await axios.get(`/api/cheapest_slots_tomorrow/${this.cheapestCount}`);
                this.slots = this.groupAndColorSlots(response.data);
                this.title = `${this.cheapestCount} cheapest slots for tomorrow only`;
            } catch (error) {
                console.error('Error fetching cheapest slots for tomorrow:', error);
            }
        },
        groupAndColorSlots(slots) {
            // Sort slots by price to determine color classes
            const sortedByPrice = [...slots].sort((a, b) => a.value_inc_vat - b.value_inc_vat);
            
            // Define color classes
            const colorClasses = ['bg-green', 'bg-light-green', 'bg-yellow', 'bg-light-red', 'bg-red'];
            
            // Calculate segment size
            const segmentSize = Math.ceil(sortedByPrice.length / 5);
            
            // Create a map of value_inc_vat to color class
            const priceColorMap = new Map(
                sortedByPrice.map((slot, index) => [
                    slot.value_inc_vat, 
                    colorClasses[Math.floor(index / segmentSize)]
                ])
            );

            // Get today's and tomorrow's dates
            const today = new Date().toLocaleDateString();
            const tomorrow = new Date(new Date().setDate(new Date().getDate() + 1)).toLocaleDateString();

            // Group slots by date and assign colors
            const grouped = {};
            slots.forEach((slot) => {
                const date = new Date(slot.valid_from);
                let dateKey = date.toLocaleDateString();
                if (dateKey === today) {
                    dateKey = 'Today';
                } else if (dateKey === tomorrow) {
                    dateKey = 'Tomorrow';
                }
                const time = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                if (!grouped[dateKey]) {
                    grouped[dateKey] = [];
                }
                grouped[dateKey].push({
                    time,
                    value: parseFloat(slot.value_inc_vat).toFixed(1),
                    colorClass: priceColorMap.get(slot.value_inc_vat)
                });
            });

            // Sort slots within each date
            for (const date in grouped) {
                grouped[date].sort((a, b) => new Date('1970/01/01 ' + a.time) - new Date('1970/01/01 ' + b.time));
            }

            // Ensure 'Today' and 'Tomorrow' are at the beginning if they exist
            const orderedGrouped = {};
            if ('Today' in grouped) orderedGrouped['Today'] = grouped['Today'];
            if ('Tomorrow' in grouped) orderedGrouped['Tomorrow'] = grouped['Tomorrow'];
            Object.keys(grouped).sort().forEach(key => {
                if (key !== 'Today' && key !== 'Tomorrow') {
                    orderedGrouped[key] = grouped[key];
                }
            });

            return orderedGrouped;
        },
        toggleApiDetails() {
            this.showApiDetails = !this.showApiDetails;
        }
    },
    mounted() {
        // Load all slots by default when the component is mounted
        this.fetchAllSlots();
    }
});